import re
from datetime import timedelta

from flask import current_app

from database.db import db
from models import serialize_datetime, utcnow
from models.otp_model import OtpModel, OtpRateLimitModel
from models.user_model import UserModel
from services.sms_service import sms_service
from utils.hash_helper import hash_password, verify_password
from utils.jwt_helper import generate_token
from utils.otp_helper import generate_otp, get_otp_expiry, mask_phone
from utils.response_helper import AppError


class AuthService:
    @property
    def users_collection(self):
        return db.get_collection("users")

    @property
    def otp_collection(self):
        return db.get_collection("otps")

    @property
    def otp_rate_limits_collection(self):
        return db.get_collection("otp_rate_limits")

    @staticmethod
    def normalize_phone(phone):
        normalized = re.sub(r"\D", "", phone or "")
        if len(normalized) < 10 or len(normalized) > 15:
            raise AppError("Enter a valid phone number.", 400)
        return normalized

    @staticmethod
    def normalize_name(name):
        cleaned = (name or "").strip()
        if len(cleaned) < 2:
            raise AppError("Name must be at least 2 characters long.", 400)
        return cleaned

    @staticmethod
    def normalize_user_id(user_id):
        cleaned = (user_id or "").strip()
        if not cleaned:
            raise AppError("User ID is required.", 400)
        return cleaned

    @staticmethod
    def normalize_address(address):
        cleaned = " ".join((address or "").split())
        if len(cleaned) < 10:
            raise AppError("Address must be at least 10 characters long.", 400)
        if len(cleaned) > 250:
            raise AppError("Address must be 250 characters or fewer.", 400)
        return cleaned

    @staticmethod
    def validate_password(password):
        if not password or len(password) < 8:
            raise AppError("Password must be at least 8 characters long.", 400)
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise AppError("Password must include letters and numbers.", 400)
        return password

    @staticmethod
    def _build_session_payload(user_document):
        session_token = generate_token(
            user_document,
            current_app.config["JWT_SECRET_KEY"],
            current_app.config["JWT_EXPIRATION_HOURS"],
        )
        return {
            "sessionToken": session_token,
            "user": UserModel.to_public(user_document),
        }

    def _consume_otp_send_slot(self, phone):
        now = utcnow()
        window_minutes = current_app.config["OTP_RATE_LIMIT_WINDOW_MINUTES"]
        window_started_after = now - timedelta(minutes=window_minutes)
        window_expires_at = now + timedelta(minutes=window_minutes)
        max_requests = current_app.config["OTP_MAX_SENDS_PER_WINDOW"]

        active_window = self.otp_rate_limits_collection.find_one(
            {"phone": phone, "windowStartedAt": {"$gt": window_started_after}}
        )
        if active_window:
            if int(active_window.get("requestCount", 0)) >= max_requests:
                raise AppError(
                    "Too many OTP requests. Please wait before requesting another code.",
                    429,
                    {
                        "maxRequestsPerWindow": max_requests,
                        "rateLimitWindowMinutes": window_minutes,
                        "retryAt": serialize_datetime(active_window.get("windowExpiresAt")),
                    },
                )

            self.otp_rate_limits_collection.update_one(
                {"_id": active_window["_id"]},
                {
                    "$inc": {"requestCount": 1},
                    "$set": {
                        "lastRequestedAt": now,
                        "windowExpiresAt": window_expires_at,
                    },
                },
            )
            return

        rate_limit_document = OtpRateLimitModel.create(phone, now, window_expires_at)
        self.otp_rate_limits_collection.update_one(
            {"phone": phone},
            {"$set": rate_limit_document},
            upsert=True,
        )

    def _rollback_otp_send_slot(self, phone):
        rate_limit_document = self.otp_rate_limits_collection.find_one({"phone": phone})
        if not rate_limit_document:
            return

        next_count = max(int(rate_limit_document.get("requestCount", 1)) - 1, 0)
        if next_count == 0:
            self.otp_rate_limits_collection.delete_one({"_id": rate_limit_document["_id"]})
            return

        self.otp_rate_limits_collection.update_one(
            {"_id": rate_limit_document["_id"]},
            {"$set": {"requestCount": next_count}},
        )

    def _raise_if_attempt_limit_reached(self, otp_document):
        max_attempts = int(
            otp_document.get("maxAttempts", current_app.config["OTP_MAX_VERIFICATION_ATTEMPTS"])
        )
        if int(otp_document.get("attemptCount", 0)) >= max_attempts:
            self.otp_collection.delete_one({"_id": otp_document["_id"]})
            raise AppError(
                "Too many invalid OTP attempts. Please request a new code.",
                429,
                {"maxAttempts": max_attempts},
            )

    def _register_failed_otp_attempt(self, otp_document):
        max_attempts = int(
            otp_document.get("maxAttempts", current_app.config["OTP_MAX_VERIFICATION_ATTEMPTS"])
        )
        next_attempt_count = int(otp_document.get("attemptCount", 0)) + 1

        if next_attempt_count >= max_attempts:
            self.otp_collection.delete_one({"_id": otp_document["_id"]})
            raise AppError(
                "Too many invalid OTP attempts. Please request a new code.",
                429,
                {"maxAttempts": max_attempts},
            )

        self.otp_collection.update_one(
            {"_id": otp_document["_id"]},
            {"$set": {"attemptCount": next_attempt_count, "updatedAt": utcnow()}},
        )
        raise AppError(
            "Invalid OTP entered.",
            400,
            {"remainingAttempts": max_attempts - next_attempt_count},
        )

    def send_otp(self, payload):
        phone = self.normalize_phone(payload.get("phone"))

        existing_user = self.users_collection.find_one({"phone": phone, "role": "student"})
        if existing_user:
            raise AppError("A student account already exists for this phone number.", 409)

        self._consume_otp_send_slot(phone)

        plain_otp = generate_otp()
        otp_document = OtpModel.create(
            phone=phone,
            hashed_otp=hash_password(plain_otp),
            expires_at=get_otp_expiry(current_app.config["OTP_EXPIRY_MINUTES"]),
            max_attempts=current_app.config["OTP_MAX_VERIFICATION_ATTEMPTS"],
        )

        self.otp_collection.update_one({"phone": phone}, {"$set": otp_document}, upsert=True)
        try:
            delivery_details = sms_service.send_otp(
                phone,
                plain_otp,
                current_app.config["OTP_EXPIRY_MINUTES"],
            )
        except Exception:
            self.otp_collection.delete_many({"phone": phone})
            self._rollback_otp_send_slot(phone)
            raise

        response_payload = {
            "phone": phone,
            "maskedPhone": mask_phone(phone),
            "expiresInMinutes": current_app.config["OTP_EXPIRY_MINUTES"],
        }
        response_payload.update(delivery_details)
        if delivery_details["deliveryMode"] == "mock":
            response_payload["otpPreview"] = plain_otp

        return response_payload

    def verify_otp(self, payload):
        phone = self.normalize_phone(payload.get("phone"))
        otp = (payload.get("otp") or "").strip()

        if len(otp) != 6 or not otp.isdigit():
            raise AppError("Enter a valid 6-digit OTP.", 400)

        otp_document = self.otp_collection.find_one({"phone": phone})
        if not otp_document:
            raise AppError("No OTP request found for this phone number.", 404)

        if otp_document["expiresAt"] <= utcnow():
            self.otp_collection.delete_one({"_id": otp_document["_id"]})
            raise AppError("OTP has expired. Please request a new one.", 400)

        self._raise_if_attempt_limit_reached(otp_document)

        if not verify_password(otp, otp_document["otp"]):
            self._register_failed_otp_attempt(otp_document)

        self.otp_collection.update_one(
            {"_id": otp_document["_id"]},
            {
                "$set": {
                    "verified": True,
                    "verifiedAt": utcnow(),
                    "attemptCount": 0,
                    "updatedAt": utcnow(),
                }
            },
        )

        return {"phone": phone, "verified": True}

    def register_student(self, payload):
        name = self.normalize_name(payload.get("name"))
        phone = self.normalize_phone(payload.get("phone"))
        address = self.normalize_address(payload.get("address"))
        password = self.validate_password(payload.get("password"))

        if self.users_collection.find_one({"phone": phone}):
            raise AppError("A user already exists with this phone number.", 409)

        verified_otp = self.otp_collection.find_one(
            {"phone": phone, "verified": True, "expiresAt": {"$gt": utcnow()}}
        )
        if not verified_otp:
            raise AppError("Phone number verification is required before registration.", 400)

        user_document = UserModel.create_student(name, phone, address, hash_password(password))
        insert_result = self.users_collection.insert_one(user_document)
        user_document["_id"] = insert_result.inserted_id

        self.otp_collection.delete_many({"phone": phone})
        return self._build_session_payload(user_document)

    def login_student(self, payload):
        phone = self.normalize_phone(payload.get("phone"))
        password = payload.get("password") or ""

        user_document = self.users_collection.find_one({"phone": phone, "role": "student"})
        if not user_document or not verify_password(password, user_document["password"]):
            raise AppError("Invalid phone number or password.", 401)

        return self._build_session_payload(user_document)

    def login_staff(self, payload):
        user_id = self.normalize_user_id(payload.get("userId"))
        password = payload.get("password") or ""

        user_document = self.users_collection.find_one(
            {"userId": user_id, "role": {"$in": ["admin", "delivery"]}}
        )
        if not user_document or not verify_password(password, user_document["password"]):
            raise AppError("Invalid staff credentials.", 401)

        return self._build_session_payload(user_document)


auth_service = AuthService()
