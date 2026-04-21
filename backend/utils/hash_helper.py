import bcrypt


def hash_password(raw_value):
    return bcrypt.hashpw(raw_value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_value, hashed_value):
    return bcrypt.checkpw(raw_value.encode("utf-8"), hashed_value.encode("utf-8"))
