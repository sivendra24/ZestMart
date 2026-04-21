from flask import g, request

from services.order_service import order_service
from utils.response_helper import success_response


def create_order():
    payload = request.get_json(silent=True) or {}
    result = order_service.create_order(g.current_user, payload)
    return success_response("Order created successfully.", result, 201)


def get_orders():
    result = order_service.get_orders(g.current_user)
    return success_response("Orders fetched successfully.", result)


def update_order_status(order_id):
    payload = request.get_json(silent=True) or {}
    result = order_service.update_order_status(order_id, payload, g.current_user)
    return success_response("Order status updated successfully.", result)
