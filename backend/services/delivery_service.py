from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ReturnDocument

from database.db import db
from models import utcnow
from models.order_model import OrderModel
from utils.response_helper import AppError


class DeliveryService:
    @property
    def orders_collection(self):
        return db.get_collection("orders")

    @staticmethod
    def _parse_order_id(order_id):
        try:
            return ObjectId(order_id)
        except (InvalidId, TypeError):
            raise AppError("Invalid order ID.", 400)

    def get_dashboard_orders(self, actor):
        pending_orders = self.orders_collection.find({"status": "pending"}).sort("createdAt", -1)
        assigned_query = (
            {"status": {"$in": ["assigned", "delivered"]}}
            if actor["role"] == "admin"
            else {"deliveryPersonId": actor["id"]}
        )
        assigned_orders = self.orders_collection.find(assigned_query).sort("createdAt", -1)

        return {
            "pendingOrders": [OrderModel.serialize(order) for order in pending_orders],
            "assignedOrders": [OrderModel.serialize(order) for order in assigned_orders],
        }

    def accept_order(self, order_id, actor):
        if actor["role"] != "delivery":
            raise AppError("Only delivery personnel can accept pending orders.", 403)

        object_id = self._parse_order_id(order_id)

        updated_order = self.orders_collection.find_one_and_update(
            {"_id": object_id, "status": "pending"},
            {
                "$set": {
                    "status": "assigned",
                    "deliveryPersonId": actor["id"],
                    "deliveryPersonUserId": actor.get("userId"),
                    "deliveryPersonName": actor["name"],
                    "updatedAt": utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        if not updated_order:
            raise AppError("Order was already assigned or does not exist.", 409)

        return OrderModel.serialize(updated_order)


delivery_service = DeliveryService()
