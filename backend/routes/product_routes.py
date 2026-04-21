from flask import Blueprint

from controllers.product_controller import list_products


product_bp = Blueprint("products", __name__)

product_bp.get("/products")(list_products)
