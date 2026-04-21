import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone

from flask import g, has_request_context, request


request_logger = logging.getLogger("zestmart.request")


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _client_ip():
    access_route = request.access_route
    if access_route:
        return access_route[0]
    return request.remote_addr


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": _utc_timestamp(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra_fields = getattr(record, "extra_fields", None) or {}
        payload.update(extra_fields)

        if has_request_context():
            payload.setdefault("requestId", getattr(g, "request_id", None))
            payload.setdefault("method", request.method)
            payload.setdefault("path", request.path)
            payload.setdefault("clientIp", _client_ip())

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level):
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def register_request_logging(app):
    @app.before_request
    def attach_request_context():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_started_at = time.perf_counter()

    @app.after_request
    def log_response(response):
        duration_ms = round((time.perf_counter() - g.request_started_at) * 1000, 2)
        response.headers["X-Request-ID"] = g.request_id
        request_logger.info(
            "request_completed",
            extra={
                "extra_fields": {
                    "requestId": g.request_id,
                    "method": request.method,
                    "path": request.path,
                    "statusCode": response.status_code,
                    "durationMs": duration_ms,
                    "clientIp": _client_ip(),
                }
            },
        )
        return response
