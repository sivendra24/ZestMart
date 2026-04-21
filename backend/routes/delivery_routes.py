from flask import Blueprint

from controllers.delivery_controller import accept_delivery_order, get_delivery_orders
from middleware.auth_middleware import auth_required
from middleware.role_middleware import roles_required


delivery_bp = Blueprint("delivery", __name__, url_prefix="/delivery")


@delivery_bp.get("/orders")
@auth_required
@roles_required("delivery", "admin")
def get_delivery_orders_route():
    return get_delivery_orders()


@delivery_bp.put("/orders/<string:order_id>/accept")
@auth_required
@roles_required("delivery")
def accept_delivery_order_route(order_id):
    return accept_delivery_order(order_id)
