from functools import wraps

from flask import g

from utils.response_helper import AppError


def roles_required(*allowed_roles):
    def decorator(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            current_user = getattr(g, "current_user", None)
            if not current_user:
                raise AppError("Authentication is required.", 401)

            if current_user["role"] not in allowed_roles:
                raise AppError("You do not have permission to access this resource.", 403)

            return handler(*args, **kwargs)

        return wrapper

    return decorator
