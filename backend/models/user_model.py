from models import serialize_datetime, utcnow


class UserModel:
    @staticmethod
    def create_student(name, phone, address, hashed_password):
        return {
            "name": name,
            "phone": phone,
            "address": address,
            "password": hashed_password,
            "role": "student",
            "isVerified": True,
            "createdAt": utcnow(),
        }

    @staticmethod
    def create_staff(name, user_id, hashed_password, role):
        return {
            "name": name,
            "userId": user_id,
            "password": hashed_password,
            "role": role,
            "isVerified": True,
            "createdAt": utcnow(),
        }

    @staticmethod
    def to_public(document):
        return {
            "id": str(document["_id"]),
            "name": document.get("name"),
            "phone": document.get("phone"),
            "address": document.get("address"),
            "userId": document.get("userId"),
            "role": document.get("role"),
            "isVerified": bool(document.get("isVerified", False)),
            "createdAt": serialize_datetime(document.get("createdAt")),
        }
