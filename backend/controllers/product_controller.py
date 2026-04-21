from flask import g, request

from services.product_service import product_service
from utils.response_helper import success_response


def _get_product_payload():
    if request.mimetype and request.mimetype.startswith("multipart/form-data"):
        return request.form.to_dict()
    return request.get_json(silent=True) or {}


def list_products():
    result = product_service.list_products()
    return success_response("Products fetched successfully.", result)


def create_product():
    payload = _get_product_payload()
    result = product_service.add_product(payload, g.current_user, request.files.get("image"))
    return success_response("Product created successfully.", result, 201)


def update_product(product_id):
    payload = request.get_json(silent=True) or {}
    result = product_service.update_product(product_id, payload, g.current_user)
    return success_response("Product updated successfully.", result)


def delete_product(product_id):
    product_service.delete_product(product_id, g.current_user)
    return success_response("Product deleted successfully.", {})


def update_product_image(product_id):
    result = product_service.update_product_image(product_id, g.uploaded_file, g.current_user)
    return success_response("Product image updated successfully.", result)
