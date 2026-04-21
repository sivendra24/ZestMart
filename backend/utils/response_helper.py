import logging

from flask import g, has_request_context, jsonify
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import RequestEntityTooLarge


logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message, status_code=400, data=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = {} if data is None else data


def success_response(message, data=None, status_code=200):
    return (
        jsonify(
            {
                "success": True,
                "message": message,
                "data": {} if data is None else data,
            }
        ),
        status_code,
    )


def error_response(message, data=None, status_code=400):
    payload_data = {} if data is None else dict(data)
    if has_request_context() and getattr(g, "request_id", None):
        payload_data.setdefault("requestId", g.request_id)

    return (
        jsonify(
            {
                "success": False,
                "message": message,
                "data": payload_data,
            }
        ),
        status_code,
    )


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return error_response(error.message, error.data, error.status_code)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_large_upload(_error):
        return error_response("Uploaded file exceeds the configured size limit.", status_code=413)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit(error):
        retry_after = getattr(error, "retry_after", None)
        data = {}
        if retry_after is not None:
            data["retryAfterSeconds"] = retry_after
        return error_response("Too many requests. Please try again later.", data, 429)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return error_response("The requested resource was not found.", status_code=404)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled application error: %s", error)
        return error_response("An unexpected server error occurred.", status_code=500)
