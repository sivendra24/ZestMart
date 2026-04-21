from flask import Blueprint

from controllers.product_controller import (
    create_product,
    delete_product,
    update_product,
    update_product_image,
)
from middleware.auth_middleware import auth_required
from middleware.role_middleware import roles_required
from middleware.upload_middleware import file_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.post("/products")
@auth_required
@roles_required("admin")
def create_product_route():
    return create_product()


@admin_bp.put("/products/<string:product_id>")
@auth_required
@roles_required("admin")
def update_product_route(product_id):
    return update_product(product_id)


@admin_bp.delete("/products/<string:product_id>")
@auth_required
@roles_required("admin")
def delete_product_route(product_id):
    return delete_product(product_id)


@admin_bp.put("/products/<string:product_id>/image")
@auth_required
@roles_required("admin")
@file_required("image")
def update_product_image_route(product_id):
    return update_product_image(product_id)
