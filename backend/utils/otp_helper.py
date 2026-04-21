import secrets
from datetime import timedelta

from models import utcnow


def generate_otp(length=6):
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def get_otp_expiry(minutes):
    return utcnow() + timedelta(minutes=minutes)


def mask_phone(phone):
    visible_tail = phone[-4:] if phone else ""
    return f"{'*' * max(len(phone) - 4, 0)}{visible_tail}"
