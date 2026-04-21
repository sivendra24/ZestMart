from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def serialize_datetime(value):
    return value.isoformat() if isinstance(value, datetime) else value
