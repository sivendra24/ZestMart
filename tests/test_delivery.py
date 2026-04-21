import pytest
from bson import ObjectId

from database.db import db
from services.delivery_service import delivery_service
from utils.response_helper import AppError


def test_accept_order_rejects_admin_actor(app):
    order_id = ObjectId()
    db.get_collection("orders").insert_one(
        {
            "_id": order_id,
            "status": "pending",
            "deliveryPersonId": None,
            "deliveryPersonUserId": None,
            "deliveryPersonName": None,
        }
    )

    with app.app_context():
        with pytest.raises(AppError) as error:
            delivery_service.accept_order(
                str(order_id),
                {"id": "admin-1", "role": "admin", "name": "ZestMart Admin", "userId": "admin001"},
            )

    assert error.value.status_code == 403
    stored_order = db.get_collection("orders").find_one({"_id": order_id})
    assert stored_order["status"] == "pending"
    assert stored_order["deliveryPersonId"] is None


def test_accept_order_assigns_delivery_user(app):
    order_id = ObjectId()
    db.get_collection("orders").insert_one(
        {
            "_id": order_id,
            "status": "pending",
            "deliveryPersonId": None,
            "deliveryPersonUserId": None,
            "deliveryPersonName": None,
        }
    )

    actor = {
        "id": "delivery-user-id",
        "role": "delivery",
        "name": "Rapid Rider",
        "userId": "delivery001",
    }

    with app.app_context():
        response = delivery_service.accept_order(str(order_id), actor)

    assert response["status"] == "assigned"
    assert response["deliveryPersonId"] == actor["id"]
    assert response["deliveryPersonUserId"] == actor["userId"]
    assert response["deliveryPersonName"] == actor["name"]
