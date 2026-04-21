from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from utils.response_helper import AppError


IMAGE_FORMATS = {
    "JPEG": {"mime": "image/jpeg", "extension": ".jpg"},
    "PNG": {"mime": "image/png", "extension": ".png"},
    "WEBP": {"mime": "image/webp", "extension": ".webp"},
}


def allowed_file(filename, allowed_extensions):
    extension = Path(filename).suffix.lower().lstrip(".")
    return bool(extension) and extension in set(allowed_extensions)


def validate_image_upload(uploaded_file, allowed_extensions, allowed_mime_types, max_pixels):
    filename = secure_filename(uploaded_file.filename or "")
    if not filename:
        raise AppError("Invalid image filename.", 400)

    if not allowed_file(filename, allowed_extensions):
        raise AppError("Unsupported image format.", 400)

    reported_mime = (uploaded_file.mimetype or "").lower()
    if reported_mime not in set(allowed_mime_types):
        raise AppError("Unsupported image MIME type.", 400)

    try:
        Image.MAX_IMAGE_PIXELS = int(max_pixels)
        uploaded_file.stream.seek(0)
        with Image.open(uploaded_file.stream) as image:
            image.verify()

        uploaded_file.stream.seek(0)
        with Image.open(uploaded_file.stream) as image:
            if image.width * image.height > int(max_pixels):
                raise AppError("Image dimensions exceed the configured safety limit.", 400)

            image_format = (image.format or "").upper()
    except AppError:
        raise
    except (UnidentifiedImageError, OSError):
        raise AppError("Uploaded file is not a valid image.", 400)
    finally:
        uploaded_file.stream.seek(0)

    if image_format not in IMAGE_FORMATS:
        raise AppError("Unsupported image format.", 400)

    detected_mime = IMAGE_FORMATS[image_format]["mime"]
    if detected_mime not in set(allowed_mime_types):
        raise AppError("Unsupported image MIME type.", 400)

    return IMAGE_FORMATS[image_format]["extension"]


def save_upload(uploaded_file, upload_dir, allowed_extensions, allowed_mime_types, max_pixels):
    safe_extension = validate_image_upload(
        uploaded_file,
        allowed_extensions,
        allowed_mime_types,
        max_pixels,
    )
    saved_name = f"{uuid4().hex}{safe_extension}"
    destination = Path(upload_dir) / saved_name
    destination.parent.mkdir(parents=True, exist_ok=True)
    uploaded_file.stream.seek(0)
    uploaded_file.save(destination)
    return f"/uploads/products/{saved_name}"


def delete_upload(image_url, upload_dir):
    if not image_url:
        return

    target_file = Path(upload_dir) / Path(image_url).name
    if target_file.exists() and target_file.is_file():
        target_file.unlink()
