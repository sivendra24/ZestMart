from models import serialize_datetime, utcnow


class ProductModel:
    @staticmethod
    def create(payload):
        timestamp = utcnow()
        return {
            "name": payload["name"],
            "price": round(float(payload["price"]), 2),
            "category": payload["category"],
            "stock": int(payload["stock"]),
            "imageUrl": payload.get("imageUrl"),
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }

    @staticmethod
    def serialize(document):
        return {
            "id": str(document["_id"]),
            "name": document.get("name"),
            "price": round(float(document.get("price", 0)), 2),
            "category": document.get("category"),
            "stock": int(document.get("stock", 0)),
            "imageUrl": document.get("imageUrl"),
            "createdAt": serialize_datetime(document.get("createdAt")),
            "updatedAt": serialize_datetime(document.get("updatedAt")),
        }
