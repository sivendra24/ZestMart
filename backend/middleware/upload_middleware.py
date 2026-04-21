from functools import wraps

from flask import current_app, g, request

from utils.file_helper import validate_image_upload
from utils.response_helper import AppError


def file_required(field_name="image"):
    def decorator(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            uploaded_file = request.files.get(field_name)
            if not uploaded_file or not uploaded_file.filename:
                raise AppError("An image file is required.", 400)

            validate_image_upload(
                uploaded_file,
                current_app.config["ALLOWED_IMAGE_EXTENSIONS"],
                current_app.config["ALLOWED_IMAGE_MIME_TYPES"],
                current_app.config["MAX_IMAGE_PIXELS"],
            )

            g.uploaded_file = uploaded_file
            return handler(*args, **kwargs)

        return wrapper

    return decorator
