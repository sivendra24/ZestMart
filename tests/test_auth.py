import importlib.util
from pathlib import Path

import dotenv
import pytest
from bson import ObjectId

from flask import g, jsonify

from database.db import db
from middleware.auth_middleware import auth_required
from models.otp_model import OtpModel
from services.auth_service import auth_service
from utils.hash_helper import hash_password
from utils.otp_helper import get_otp_expiry
from utils.jwt_helper import clear_auth_cookie, decode_token, generate_token, set_auth_cookie
from utils.response_helper import AppError


ROOT = Path(__file__).resolve().parents[1]


def test_generate_and_decode_token_round_trip():
    user_document = {
        "_id": ObjectId(),
        "role": "student",
        "phone": "9876543210",
        "userId": None,
    }

    token = generate_token(user_document, "jwt-test-secret", 1)
    payload = decode_token(token, "jwt-test-secret")

    assert payload["sub"] == str(user_document["_id"])
    assert payload["role"] == "student"
    assert payload["phone"] == "9876543210"


def test_auth_cookie_is_http_only_and_secure_flags_are_applied(app):
    with app.app_context():
        response = app.make_response(("ok", 200))
        set_auth_cookie(response, "signed-token", app.config)
        cookie_header = response.headers.get("Set-Cookie")

        assert "HttpOnly" in cookie_header
        assert "SameSite=Lax" in cookie_header
        assert "zestmart_session=signed-token" in cookie_header

        clear_auth_cookie(response, app.config)
        cleared_cookie_headers = response.headers.getlist("Set-Cookie")
        assert any("zestmart_session=" in header for header in cleared_cookie_headers)


def test_auth_required_reads_jwt_from_cookie(app):
    user_document = {
        "_id": ObjectId(),
        "name": "Campus Shopper",
        "phone": "9876543210",
        "address": "Boys Hostel Block A, Room 204, North Campus",
        "password": hash_password("Student@123"),
        "role": "student",
        "isVerified": True,
    }
    db.get_collection("users").insert_one(user_document)

    @app.get("/protected")
    @auth_required
    def protected():
        return jsonify({"userId": g.current_user["id"]})

    token = generate_token(user_document, app.config["JWT_SECRET_KEY"], 1)
    client = app.test_client()
    client.set_cookie(app.config["JWT_COOKIE_NAME"], token)

    response = client.get("/protected")
    assert response.status_code == 200
    assert response.get_json()["userId"] == str(user_document["_id"])


def test_config_requires_explicit_secrets(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)

    spec = importlib.util.spec_from_file_location(
        "config_missing_secret_test", ROOT / "backend" / "config.py"
    )
    config_module = importlib.util.module_from_spec(spec)

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        spec.loader.exec_module(config_module)


def test_send_otp_enforces_rate_limit(app):
    with app.app_context():
        for _ in range(app.config["OTP_MAX_SENDS_PER_WINDOW"]):
            response = auth_service.send_otp({"phone": "9876543210"})
            assert response["deliveryMode"] == "mock"

        with pytest.raises(AppError) as error:
            auth_service.send_otp({"phone": "9876543210"})

    assert error.value.status_code == 429
    assert error.value.data["maxRequestsPerWindow"] == app.config["OTP_MAX_SENDS_PER_WINDOW"]
    assert error.value.data["rateLimitWindowMinutes"] == app.config["OTP_RATE_LIMIT_WINDOW_MINUTES"]


def test_verify_otp_caps_invalid_attempts(app):
    with app.app_context():
        otp_document = OtpModel.create(
            phone="9876543210",
            hashed_otp=hash_password("123456"),
            expires_at=get_otp_expiry(app.config["OTP_EXPIRY_MINUTES"]),
            max_attempts=app.config["OTP_MAX_VERIFICATION_ATTEMPTS"],
        )
        db.get_collection("otps").insert_one(otp_document)

        with pytest.raises(AppError) as first_error:
            auth_service.verify_otp({"phone": "9876543210", "otp": "000000"})

        assert first_error.value.status_code == 400
        assert first_error.value.data["remainingAttempts"] == 2

        with pytest.raises(AppError) as second_error:
            auth_service.verify_otp({"phone": "9876543210", "otp": "000000"})

        assert second_error.value.status_code == 400
        assert second_error.value.data["remainingAttempts"] == 1

        with pytest.raises(AppError) as final_error:
            auth_service.verify_otp({"phone": "9876543210", "otp": "000000"})

        assert final_error.value.status_code == 429
        assert db.get_collection("otps").find_one({"phone": "9876543210"}) is None
