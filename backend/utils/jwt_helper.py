from datetime import timedelta

import jwt

from models import utcnow
from utils.response_helper import AppError


def generate_token(user_document, secret, expiration_hours):
    issued_at = utcnow()
    payload = {
        "sub": str(user_document["_id"]),
        "role": user_document["role"],
        "phone": user_document.get("phone"),
        "userId": user_document.get("userId"),
        "iat": issued_at,
        "exp": issued_at + timedelta(hours=expiration_hours),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def get_request_token(request, cookie_name):
    cookie_token = (request.cookies.get(cookie_name) or "").strip()
    if cookie_token:
        return cookie_token

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return ""


def set_auth_cookie(response, token, config):
    response.set_cookie(
        config["JWT_COOKIE_NAME"],
        token,
        max_age=int(config["JWT_EXPIRATION_HOURS"] * 60 * 60),
        httponly=True,
        secure=config["JWT_COOKIE_SECURE"],
        samesite=config["JWT_COOKIE_SAMESITE"],
        domain=config["JWT_COOKIE_DOMAIN"],
        path="/",
    )


def clear_auth_cookie(response, config):
    response.delete_cookie(
        config["JWT_COOKIE_NAME"],
        httponly=True,
        secure=config["JWT_COOKIE_SECURE"],
        samesite=config["JWT_COOKIE_SAMESITE"],
        domain=config["JWT_COOKIE_DOMAIN"],
        path="/",
    )


def decode_token(token, secret):
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise AppError("Your session has expired. Please sign in again.", 401)
    except jwt.InvalidTokenError:
        raise AppError("Invalid authentication token.", 401)
