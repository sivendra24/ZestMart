from flask import Blueprint

from controllers.order_controller import create_order, get_orders, update_order_status
from middleware.auth_middleware import auth_required
from middleware.role_middleware import roles_required


order_bp = Blueprint("orders", __name__, url_prefix="/orders")


@order_bp.post("")
@auth_required
@roles_required("student", "delivery", "admin")
def create_order_route():
    return create_order()


@order_bp.get("")
@auth_required
@roles_required("student", "delivery", "admin")
def get_orders_route():
    return get_orders()


@order_bp.put("/<string:order_id>/status")
@auth_required
@roles_required("delivery", "admin")
def update_order_status_route(order_id):
    return update_order_status(order_id)
