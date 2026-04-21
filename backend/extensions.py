import re

from flask import request
from flask_limiter import Limiter


def rate_limit_key():
    forwarded_for = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    remote_addr = forwarded_for or request.remote_addr or "unknown"

    identifier = ""
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        identifier = payload.get("phone") or payload.get("userId") or ""
    elif request.form:
        identifier = request.form.get("phone") or request.form.get("userId") or ""

    safe_identifier = re.sub(r"\s+", "", str(identifier)).lower() or "anonymous"
    return f"{remote_addr}:{safe_identifier}"


limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=[],
)
