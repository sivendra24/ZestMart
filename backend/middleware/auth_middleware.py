from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app, g, request

from database.db import db
from models.user_model import UserModel
from utils.jwt_helper import decode_token, get_request_token
from utils.response_helper import AppError


def auth_required(handler):
    @wraps(handler)
    def wrapper(*args, **kwargs):
        token = get_request_token(request, current_app.config["JWT_COOKIE_NAME"])
        if not token:
            raise AppError("Authentication token is required.", 401)

        payload = decode_token(token, current_app.config["JWT_SECRET_KEY"])

        try:
            user_id = ObjectId(payload["sub"])
        except (InvalidId, KeyError, TypeError):
            raise AppError("Invalid authentication token.", 401)

        user_document = db.get_collection("users").find_one({"_id": user_id})
        if not user_document:
            raise AppError("Authenticated user no longer exists.", 401)

        g.current_user_raw = user_document
        g.current_user = UserModel.to_public(user_document)
        return handler(*args, **kwargs)

    return wrapper
