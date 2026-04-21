from models import utcnow


class OtpModel:
    @staticmethod
    def create(phone, hashed_otp, expires_at, max_attempts):
        timestamp = utcnow()
        return {
            "phone": phone,
            "otp": hashed_otp,
            "expiresAt": expires_at,
            "verified": False,
            "verifiedAt": None,
            "attemptCount": 0,
            "maxAttempts": int(max_attempts),
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }


class OtpRateLimitModel:
    @staticmethod
    def create(phone, window_started_at, window_expires_at):
        return {
            "phone": phone,
            "requestCount": 1,
            "windowStartedAt": window_started_at,
            "windowExpiresAt": window_expires_at,
            "lastRequestedAt": window_started_at,
        }
