from models import serialize_datetime, utcnow


class OrderModel:
    @staticmethod
    def create(user, products, total_price, delivery_address):
        timestamp = utcnow()
        return {
            "userId": user["id"],
            "userRole": user["role"],
            "customerName": user["name"],
            "customerPhone": user.get("phone"),
            "deliveryAddress": delivery_address,
            "products": products,
            "totalPrice": round(float(total_price), 2),
            "status": "pending",
            "deliveryPersonId": None,
            "deliveryPersonUserId": None,
            "deliveryPersonName": None,
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }

    @staticmethod
    def serialize(document):
        return {
            "id": str(document["_id"]),
            "userId": document.get("userId"),
            "userRole": document.get("userRole"),
            "customerName": document.get("customerName"),
            "customerPhone": document.get("customerPhone"),
            "deliveryAddress": document.get("deliveryAddress"),
            "products": document.get("products", []),
            "totalPrice": round(float(document.get("totalPrice", 0)), 2),
            "status": document.get("status"),
            "deliveryPersonId": document.get("deliveryPersonId"),
            "deliveryPersonUserId": document.get("deliveryPersonUserId"),
            "deliveryPersonName": document.get("deliveryPersonName"),
            "createdAt": serialize_datetime(document.get("createdAt")),
            "updatedAt": serialize_datetime(document.get("updatedAt")),
        }
