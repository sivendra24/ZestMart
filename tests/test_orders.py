from bson import ObjectId

from database.db import db
from services.order_service import order_service


def test_create_order_persists_student_delivery_address(app):
    user_id = ObjectId()
    product_id = ObjectId()
    db.get_collection("users").insert_one(
        {
            "_id": user_id,
            "name": "Campus Shopper",
            "phone": "9876543210",
            "address": "Old Hostel Address",
            "role": "student",
            "isVerified": True,
        }
    )
    db.get_collection("products").insert_one(
        {
            "_id": product_id,
            "name": "Fresh Apples",
            "category": "Fruits",
            "price": 120,
            "stock": 5,
        }
    )

    new_address = "Boys Hostel Block C, Room 410, North Campus"

    with app.app_context():
        order = order_service.create_order(
            {
                "id": str(user_id),
                "role": "student",
                "name": "Campus Shopper",
                "phone": "9876543210",
                "address": "Old Hostel Address",
            },
            {
                "deliveryAddress": new_address,
                "products": [{"productId": str(product_id), "quantity": 2}],
            },
        )

    stored_user = db.get_collection("users").find_one({"_id": user_id})
    assert order["deliveryAddress"] == new_address
    assert stored_user["address"] == new_address
