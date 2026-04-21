import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")


INSECURE_SECRET_VALUES = {
    "change-me",
    "change-this-secret",
    "change-this-jwt-secret",
}


def get_required_secret(env_name):
    value = (os.getenv(env_name) or "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {env_name}. "
            "Set it in the project .env file before starting ZestMart."
        )

    if value.lower() in INSECURE_SECRET_VALUES:
        raise RuntimeError(
            f"Insecure value detected for {env_name}. "
            "Generate a strong random secret before starting ZestMart."
        )

    return value


def get_bool_env(env_name, default=False):
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_csv_env(env_name, default=""):
    return tuple(
        item.strip()
        for item in os.getenv(env_name, default).split(",")
        if item and item.strip()
    )


class Config:
    BASE_DIR = BASE_DIR
    PROJECT_ROOT = PROJECT_ROOT
    FRONTEND_DIR = PROJECT_ROOT / "frontend"
    FRONTEND_PAGES_DIR = FRONTEND_DIR / "pages"
    FRONTEND_CSS_DIR = FRONTEND_DIR / "css"
    FRONTEND_JS_DIR = FRONTEND_DIR / "js"
    FRONTEND_ASSETS_DIR = FRONTEND_DIR / "assets"
    UPLOAD_DIR = BASE_DIR / "uploads" / "products"
    APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

    SECRET_KEY = get_required_secret("SECRET_KEY")
    JWT_SECRET_KEY = get_required_secret("JWT_SECRET_KEY")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "12"))
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "zestmart")
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
    OTP_RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("OTP_RATE_LIMIT_WINDOW_MINUTES", "60"))
    OTP_MAX_SENDS_PER_WINDOW = int(os.getenv("OTP_MAX_SENDS_PER_WINDOW", "5"))
    OTP_MAX_VERIFICATION_ATTEMPTS = int(os.getenv("OTP_MAX_VERIFICATION_ATTEMPTS", "5"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5")) * 1024 * 1024
    MAX_IMAGE_PIXELS = int(os.getenv("MAX_IMAGE_PIXELS", "20000000"))
    MOCK_OTP_ENABLED = get_bool_env("MOCK_OTP_ENABLED", True)
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio").strip().lower()
    SMS_DEFAULT_COUNTRY_CODE = os.getenv("SMS_DEFAULT_COUNTRY_CODE", "+91").strip()
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    TWILIO_FROM_PHONE = os.getenv("TWILIO_FROM_PHONE", "").strip()
    TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "").strip()
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = get_bool_env("FLASK_DEBUG", False)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    TRUST_PROXY_COUNT = int(os.getenv("TRUST_PROXY_COUNT", "1"))
    CORS_ORIGINS = get_csv_env(
        "CORS_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000"
    )
    JWT_COOKIE_NAME = os.getenv("JWT_COOKIE_NAME", "zestmart_session").strip()
    JWT_COOKIE_DOMAIN = os.getenv("JWT_COOKIE_DOMAIN", "").strip() or None
    JWT_COOKIE_SECURE = get_bool_env("JWT_COOKIE_SECURE", APP_ENV == "production")
    JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax").strip().title()
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://").strip()
    RATELIMIT_HEADERS_ENABLED = get_bool_env("RATELIMIT_HEADERS_ENABLED", True)
    RATELIMIT_STRATEGY = os.getenv("RATELIMIT_STRATEGY", "fixed-window").strip()
    LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "10 per 15 minutes").strip()
    OTP_SEND_RATE_LIMIT = os.getenv("OTP_SEND_RATE_LIMIT", "5 per 10 minutes").strip()
    OTP_VERIFY_RATE_LIMIT = os.getenv("OTP_VERIFY_RATE_LIMIT", "10 per 10 minutes").strip()
    ALLOWED_IMAGE_EXTENSIONS = tuple(
        extension.strip().lower()
        for extension in os.getenv("ALLOWED_IMAGE_EXTENSIONS", "png,jpg,jpeg,webp").split(",")
        if extension.strip()
    )
    ALLOWED_IMAGE_MIME_TYPES = get_csv_env(
        "ALLOWED_IMAGE_MIME_TYPES",
        "image/png,image/jpeg,image/webp",
    )

    @classmethod
    def ensure_directories(cls):
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.FRONTEND_PAGES_DIR.mkdir(parents=True, exist_ok=True)
        cls.FRONTEND_CSS_DIR.mkdir(parents=True, exist_ok=True)
        cls.FRONTEND_JS_DIR.mkdir(parents=True, exist_ok=True)
        cls.FRONTEND_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_runtime_settings(cls):
        allowed_samesite_values = {"Lax", "Strict", "None"}
        if cls.JWT_COOKIE_SAMESITE not in allowed_samesite_values:
            raise RuntimeError(
                "JWT_COOKIE_SAMESITE must be one of: Lax, Strict, None."
            )

        if cls.JWT_COOKIE_SAMESITE == "None" and not cls.JWT_COOKIE_SECURE:
            raise RuntimeError(
                "JWT_COOKIE_SECURE must be true when JWT_COOKIE_SAMESITE is None."
            )

        if cls.APP_ENV == "production":
            if cls.MOCK_OTP_ENABLED:
                raise RuntimeError("MOCK_OTP_ENABLED must be false in production.")

            if not cls.CORS_ORIGINS:
                raise RuntimeError("CORS_ORIGINS must list the public site domain in production.")

            insecure_origins = {
                origin
                for origin in cls.CORS_ORIGINS
                if "localhost" in origin or "127.0.0.1" in origin
            }
            if insecure_origins:
                raise RuntimeError(
                    "CORS_ORIGINS cannot include localhost or 127.0.0.1 in production."
                )

            if not cls.JWT_COOKIE_SECURE:
                raise RuntimeError("JWT_COOKIE_SECURE must be true in production.")
