from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from database.db import db
from models import utcnow
from models.order_model import OrderModel
from models.user_model import UserModel
from utils.response_helper import AppError


class OrderService:
    @property
    def products_collection(self):
        return db.get_collection("products")

    @property
    def orders_collection(self):
        return db.get_collection("orders")

    @property
    def users_collection(self):
        return db.get_collection("users")

    @staticmethod
    def _parse_object_id(value, message):
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            raise AppError(message, 400)

    @staticmethod
    def _normalize_delivery_address(address, fallback_address=None):
        raw_value = address if address is not None else fallback_address
        cleaned = " ".join((raw_value or "").split())
        if len(cleaned) < 10:
            raise AppError("A valid delivery address is required.", 400)
        if len(cleaned) > 250:
            raise AppError("Delivery address must be 250 characters or fewer.", 400)
        return cleaned

    def create_order(self, actor, payload):
        product_items = payload.get("products") or []
        if not isinstance(product_items, list) or not product_items:
            raise AppError("At least one product is required to place an order.", 400)
        delivery_address = self._normalize_delivery_address(
            payload.get("deliveryAddress"), actor.get("address")
        )

        reserved_stock = []
        order_products = []
        total_price = 0.0

        try:
            for raw_item in product_items:
                if not isinstance(raw_item, dict):
                    raise AppError("Each ordered product must be an object.", 400)

                product_id = self._parse_object_id(raw_item.get("productId"), "Invalid product ID in order.")
                try:
                    quantity = int(raw_item.get("quantity", 0))
                except (TypeError, ValueError):
                    raise AppError("Quantity must be a valid integer.", 400)

                if quantity <= 0:
                    raise AppError("Quantity must be greater than zero.", 400)

                product_document = self.products_collection.find_one_and_update(
                    {"_id": product_id, "stock": {"$gte": quantity}},
                    {"$inc": {"stock": -quantity}, "$set": {"updatedAt": utcnow()}},
                    return_document=ReturnDocument.BEFORE,
                )
                if not product_document:
                    raise AppError("One or more products are unavailable or out of stock.", 409)

                reserved_stock.append({"productId": product_id, "quantity": quantity})

                price = round(float(product_document["price"]), 2)
                subtotal = round(price * quantity, 2)
                total_price += subtotal
                order_products.append(
                    {
                        "productId": str(product_document["_id"]),
                        "name": product_document["name"],
                        "category": product_document["category"],
                        "price": price,
                        "quantity": quantity,
                        "subtotal": subtotal,
                        "imageUrl": product_document.get("imageUrl"),
                    }
                )

            order_document = OrderModel.create(
                actor, order_products, round(total_price, 2), delivery_address
            )
            insert_result = self.orders_collection.insert_one(order_document)
            order_document["_id"] = insert_result.inserted_id
        except Exception:
            for reserved_item in reserved_stock:
                self.products_collection.update_one(
                    {"_id": reserved_item["productId"]},
                    {"$inc": {"stock": reserved_item["quantity"]}},
                )
            raise

        if actor["role"] == "student":
            self.users_collection.update_one(
                {"_id": self._parse_object_id(actor["id"], "Invalid user ID.")},
                {"$set": {"address": delivery_address, "updatedAt": utcnow()}},
            )

        return OrderModel.serialize(order_document)

    def get_orders(self, actor):
        query = {}
        if actor["role"] != "admin":
            query["userId"] = actor["id"]

        orders = self.orders_collection.find(query).sort("createdAt", -1)
        return [OrderModel.serialize(order) for order in orders]

    def update_order_status(self, order_id, payload, actor):
        object_id = self._parse_object_id(order_id, "Invalid order ID.")
        status = (payload.get("status") or "").strip().lower()

        if status not in {"pending", "assigned", "delivered"}:
            raise AppError("Status must be pending, assigned, or delivered.", 400)

        existing_order = self.orders_collection.find_one({"_id": object_id})
        if not existing_order:
            raise AppError("Order not found.", 404)

        query = {"_id": object_id}
        update_data = {"status": status, "updatedAt": utcnow()}
        unset_data = {}

        if actor["role"] == "delivery":
            if status != "delivered":
                raise AppError("Delivery personnel can only mark orders as delivered.", 403)

            query["deliveryPersonId"] = actor["id"]
            query["status"] = "assigned"
        elif actor["role"] == "admin":
            if status == "pending":
                unset_data = {
                    "deliveryPersonId": "",
                    "deliveryPersonUserId": "",
                    "deliveryPersonName": "",
                }
            elif status == "assigned":
                delivery_person_id = payload.get("deliveryPersonId")
                if not delivery_person_id and existing_order.get("deliveryPersonId"):
                    delivery_person_id = existing_order["deliveryPersonId"]

                if not delivery_person_id:
                    raise AppError(
                        "A delivery person must be selected before assigning the order.",
                        400,
                    )

                delivery_user = self.users_collection.find_one(
                    {
                        "_id": self._parse_object_id(
                            delivery_person_id, "Invalid delivery person ID."
                        ),
                        "role": "delivery",
                    }
                )
                if not delivery_user:
                    raise AppError("Delivery user not found.", 404)

                serialized_delivery_user = UserModel.to_public(delivery_user)
                update_data["deliveryPersonId"] = serialized_delivery_user["id"]
                update_data["deliveryPersonUserId"] = serialized_delivery_user.get("userId")
                update_data["deliveryPersonName"] = serialized_delivery_user["name"]
            elif status == "delivered":
                if existing_order["status"] == "pending":
                    raise AppError("Pending orders must be assigned before delivery.", 400)
        else:
            raise AppError("You do not have permission to update order status.", 403)

        update_operation = {"$set": update_data}
        if unset_data:
            update_operation["$unset"] = unset_data

        updated_order = self.orders_collection.find_one_and_update(
            query,
            update_operation,
            return_document=ReturnDocument.AFTER,
        )
        if not updated_order:
            raise AppError("Order not found or you are not allowed to update it.", 404)

        return OrderModel.serialize(updated_order)


order_service = OrderService()
