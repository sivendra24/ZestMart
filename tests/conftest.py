import os
import sys
from pathlib import Path

import mongomock
import pytest
from flask import Flask


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key")


from database.db import db


@pytest.fixture()
def app():
    app = Flask(__name__)
    app.config.update(
        APP_ENV="development",
        OTP_EXPIRY_MINUTES=5,
        OTP_RATE_LIMIT_WINDOW_MINUTES=60,
        OTP_MAX_SENDS_PER_WINDOW=5,
        OTP_MAX_VERIFICATION_ATTEMPTS=3,
        MOCK_OTP_ENABLED=True,
        SMS_PROVIDER="twilio",
        SMS_DEFAULT_COUNTRY_CODE="+91",
        TWILIO_ACCOUNT_SID="",
        TWILIO_AUTH_TOKEN="",
        TWILIO_FROM_PHONE="",
        TWILIO_MESSAGING_SERVICE_SID="",
        JWT_SECRET_KEY="test-jwt-secret-key",
        JWT_EXPIRATION_HOURS=12,
        JWT_COOKIE_NAME="zestmart_session",
        JWT_COOKIE_DOMAIN=None,
        JWT_COOKIE_SECURE=False,
        JWT_COOKIE_SAMESITE="Lax",
        CORS_ORIGINS=("http://127.0.0.1:5000",),
        RATELIMIT_STORAGE_URI="memory://",
        RATELIMIT_HEADERS_ENABLED=True,
        RATELIMIT_STRATEGY="fixed-window",
        LOGIN_RATE_LIMIT="10 per 15 minutes",
        OTP_SEND_RATE_LIMIT="5 per 10 minutes",
        OTP_VERIFY_RATE_LIMIT="10 per 10 minutes",
        UPLOAD_DIR=ROOT / "backend" / "uploads" / "products",
        ALLOWED_IMAGE_EXTENSIONS=("png", "jpg", "jpeg", "webp"),
        ALLOWED_IMAGE_MIME_TYPES=("image/png", "image/jpeg", "image/webp"),
        MAX_IMAGE_PIXELS=20000000,
        LOG_LEVEL="INFO",
        TRUST_PROXY_COUNT=1,
    )
    return app


@pytest.fixture(autouse=True)
def isolated_database():
    client = mongomock.MongoClient(tz_aware=True)
    original_client = db.client
    original_database = db.database
    db.client = client
    db.database = client["zestmart_test"]
    yield db.database
    db.client = original_client
    db.database = original_database
