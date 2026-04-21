import io

import pytest
from PIL import Image

from database.db import db
from services import product_service as product_service_module
from services.product_service import product_service
from utils.file_helper import validate_image_upload
from utils.response_helper import AppError


class DummyUpload:
    filename = "product.png"


def test_add_product_persists_optional_image_in_single_call(app, monkeypatch):
    with app.app_context():
        monkeypatch.setattr(
            product_service_module,
            "save_upload",
            lambda uploaded_file, upload_dir, allowed_extensions, allowed_mime_types, max_pixels: "/uploads/products/atomic.png",
        )

        result = product_service.add_product(
            {
                "name": "Atomic Juice",
                "category": "Beverages",
                "price": "120",
                "stock": "4",
            },
            {"role": "admin"},
            DummyUpload(),
        )

    stored_product = db.get_collection("products").find_one({"_id": db.get_collection("products").find_one()["_id"]})
    assert result["imageUrl"] == "/uploads/products/atomic.png"
    assert stored_product["imageUrl"] == "/uploads/products/atomic.png"


def test_add_product_rolls_back_saved_image_when_insert_fails(app, monkeypatch):
    deleted_images = []
    collection = db.get_collection("products")

    def failing_insert(_document):
        raise RuntimeError("insert failed")

    with app.app_context():
        monkeypatch.setattr(product_service_module, "save_upload", lambda *_args, **_kwargs: "/uploads/products/fail.png")
        monkeypatch.setattr(product_service_module, "delete_upload", lambda image_url, _upload_dir: deleted_images.append(image_url))
        monkeypatch.setattr(collection, "insert_one", failing_insert)
        monkeypatch.setattr(product_service_module.db, "get_collection", lambda _name: collection)

        with pytest.raises(RuntimeError, match="insert failed"):
            product_service.add_product(
                {
                    "name": "Rollback Juice",
                    "category": "Beverages",
                    "price": "80",
                    "stock": "6",
                },
                {"role": "admin"},
                DummyUpload(),
            )

    assert deleted_images == ["/uploads/products/fail.png"]


def test_validate_image_upload_rejects_mime_spoofing(app):
    image_stream = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(image_stream, format="PNG")
    image_stream.seek(0)

    class FakeUpload:
        filename = "avatar.png"
        mimetype = "text/plain"
        stream = image_stream

    with app.app_context():
        with pytest.raises(AppError, match="Unsupported image MIME type."):
            validate_image_upload(
                FakeUpload(),
                app.config["ALLOWED_IMAGE_EXTENSIONS"],
                app.config["ALLOWED_IMAGE_MIME_TYPES"],
                app.config["MAX_IMAGE_PIXELS"],
            )
