from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app
from pymongo import ReturnDocument

from database.db import db
from models import utcnow
from models.product_model import ProductModel
from utils.file_helper import delete_upload, save_upload
from utils.response_helper import AppError


class ProductService:
    @property
    def products_collection(self):
        return db.get_collection("products")

    @staticmethod
    def _parse_product_id(product_id):
        try:
            return ObjectId(product_id)
        except (InvalidId, TypeError):
            raise AppError("Invalid product ID.", 400)

    @staticmethod
    def _validate_payload(payload, partial=False):
        updates = {}

        if not partial or "name" in payload:
            name = (payload.get("name") or "").strip()
            if len(name) < 2:
                raise AppError("Product name must be at least 2 characters long.", 400)
            updates["name"] = name

        if not partial or "category" in payload:
            category = (payload.get("category") or "").strip()
            if len(category) < 2:
                raise AppError("Category must be at least 2 characters long.", 400)
            updates["category"] = category

        if not partial or "price" in payload:
            try:
                price = round(float(payload.get("price")), 2)
            except (TypeError, ValueError):
                raise AppError("Price must be a valid number.", 400)
            if price < 0:
                raise AppError("Price cannot be negative.", 400)
            updates["price"] = price

        if not partial or "stock" in payload:
            try:
                stock = int(payload.get("stock"))
            except (TypeError, ValueError):
                raise AppError("Stock must be a valid integer.", 400)
            if stock < 0:
                raise AppError("Stock cannot be negative.", 400)
            updates["stock"] = stock

        return updates

    def list_products(self):
        products = self.products_collection.find().sort("createdAt", -1)
        return [ProductModel.serialize(product) for product in products]

    def add_product(self, payload, actor, uploaded_file=None):
        if actor["role"] != "admin":
            raise AppError("Only admin users can create products.", 403)

        validated_payload = self._validate_payload(payload)
        image_url = None

        if uploaded_file and uploaded_file.filename:
            image_url = save_upload(
                uploaded_file,
                current_app.config["UPLOAD_DIR"],
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
                current_app.config["ALLOWED_IMAGE_MIME_TYPES"],
                current_app.config["MAX_IMAGE_PIXELS"],
            )

        product_document = ProductModel.create({**validated_payload, "imageUrl": image_url})
        try:
            insert_result = self.products_collection.insert_one(product_document)
        except Exception:
            delete_upload(image_url, current_app.config["UPLOAD_DIR"])
            raise

        product_document["_id"] = insert_result.inserted_id
        return ProductModel.serialize(product_document)

    def update_product(self, product_id, payload, actor):
        if actor["role"] != "admin":
            raise AppError("Only admin users can update products.", 403)

        object_id = self._parse_product_id(product_id)
        updates = self._validate_payload(payload, partial=True)
        if not updates:
            raise AppError("No product changes were provided.", 400)

        updates["updatedAt"] = utcnow()
        updated_product = self.products_collection.find_one_and_update(
            {"_id": object_id},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        if not updated_product:
            raise AppError("Product not found.", 404)

        return ProductModel.serialize(updated_product)

    def delete_product(self, product_id, actor):
        if actor["role"] != "admin":
            raise AppError("Only admin users can delete products.", 403)

        object_id = self._parse_product_id(product_id)
        product_document = self.products_collection.find_one({"_id": object_id})
        if not product_document:
            raise AppError("Product not found.", 404)

        delete_upload(product_document.get("imageUrl"), current_app.config["UPLOAD_DIR"])
        self.products_collection.delete_one({"_id": object_id})

    def update_product_image(self, product_id, uploaded_file, actor):
        if actor["role"] != "admin":
            raise AppError("Only admin users can update product images.", 403)

        object_id = self._parse_product_id(product_id)
        product_document = self.products_collection.find_one({"_id": object_id})
        if not product_document:
            raise AppError("Product not found.", 404)

        image_url = save_upload(
            uploaded_file,
            current_app.config["UPLOAD_DIR"],
            current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
            current_app.config["ALLOWED_IMAGE_MIME_TYPES"],
            current_app.config["MAX_IMAGE_PIXELS"],
        )
        try:
            updated_product = self.products_collection.find_one_and_update(
                {"_id": object_id},
                {"$set": {"imageUrl": image_url, "updatedAt": utcnow()}},
                return_document=ReturnDocument.AFTER,
            )
        except Exception:
            delete_upload(image_url, current_app.config["UPLOAD_DIR"])
            raise

        if not updated_product:
            delete_upload(image_url, current_app.config["UPLOAD_DIR"])
            raise AppError("Product not found.", 404)

        delete_upload(product_document.get("imageUrl"), current_app.config["UPLOAD_DIR"])
        return ProductModel.serialize(updated_product)


product_service = ProductService()
