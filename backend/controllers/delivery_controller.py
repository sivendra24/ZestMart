from flask import g

from services.delivery_service import delivery_service
from utils.response_helper import success_response


def get_delivery_orders():
    result = delivery_service.get_dashboard_orders(g.current_user)
    return success_response("Delivery orders fetched successfully.", result)


def accept_delivery_order(order_id):
    result = delivery_service.accept_order(order_id, g.current_user)
    return success_response("Order accepted successfully.", result)
