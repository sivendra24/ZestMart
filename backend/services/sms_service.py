import base64
import json
import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flask import current_app

from utils.response_helper import AppError


logger = logging.getLogger(__name__)


class SmsService:
    def send_otp(self, phone, otp, expires_in_minutes):
        if current_app.config["MOCK_OTP_ENABLED"]:
            logger.info("Mock OTP delivery enabled for %s", self.mask_phone(phone))
            return {"deliveryMode": "mock", "provider": "mock"}

        provider = current_app.config["SMS_PROVIDER"]
        if provider != "twilio":
            raise AppError(
                f"Unsupported SMS provider configured: {provider}.",
                500,
            )

        return self._send_via_twilio(phone, otp, expires_in_minutes)

    def _send_via_twilio(self, phone, otp, expires_in_minutes):
        account_sid = (current_app.config["TWILIO_ACCOUNT_SID"] or "").strip()
        auth_token = (current_app.config["TWILIO_AUTH_TOKEN"] or "").strip()
        from_phone = (current_app.config["TWILIO_FROM_PHONE"] or "").strip()
        messaging_service_sid = (current_app.config["TWILIO_MESSAGING_SERVICE_SID"] or "").strip()

        missing_settings = []
        if not account_sid:
            missing_settings.append("TWILIO_ACCOUNT_SID")
        if not auth_token:
            missing_settings.append("TWILIO_AUTH_TOKEN")
        if not from_phone and not messaging_service_sid:
            missing_settings.append("TWILIO_FROM_PHONE or TWILIO_MESSAGING_SERVICE_SID")

        if missing_settings:
            raise AppError(
                "SMS delivery is not configured. Add the missing Twilio settings or enable "
                "MOCK_OTP_ENABLED for local testing.",
                503,
                {"missingSettings": missing_settings},
            )

        request_body = {
            "To": self.format_e164_phone(phone),
            "Body": (
                f"{otp} is your ZestMart OTP. "
                f"It expires in {expires_in_minutes} minutes. "
                "Do not share this code."
            ),
        }
        if messaging_service_sid:
            request_body["MessagingServiceSid"] = messaging_service_sid
        elif from_phone:
            request_body["From"] = from_phone

        basic_auth = base64.b64encode(f"{account_sid}:{auth_token}".encode("utf-8")).decode("ascii")
        request = Request(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            data=urlencode(request_body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Basic {basic_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            logger.error("Twilio SMS request failed for %s: %s", self.mask_phone(phone), response_body)
            raise AppError(
                "Unable to send OTP SMS right now. Please try again in a moment.",
                502,
            ) from error
        except URLError as error:
            logger.error("Twilio SMS network error for %s: %s", self.mask_phone(phone), error)
            raise AppError(
                "Unable to reach the SMS gateway right now. Please try again in a moment.",
                502,
            ) from error

        logger.info("OTP SMS queued successfully for %s", self.mask_phone(phone))
        return {
            "deliveryMode": "sms",
            "provider": "twilio",
            "messageSid": payload.get("sid"),
        }

    def format_e164_phone(self, phone):
        digits = re.sub(r"\D", "", phone or "")
        default_country_code = re.sub(
            r"\D", "", current_app.config["SMS_DEFAULT_COUNTRY_CODE"] or ""
        )

        if len(digits) == 10:
            if not default_country_code:
                raise AppError("SMS default country code is not configured.", 500)
            digits = f"{default_country_code}{digits}"

        if len(digits) < 11 or len(digits) > 15:
            raise AppError("Enter a valid phone number.", 400)

        return f"+{digits}"

    @staticmethod
    def mask_phone(phone):
        visible_tail = phone[-4:] if phone else ""
        return f"{'*' * max(len(phone) - 4, 0)}{visible_tail}"


sms_service = SmsService()
