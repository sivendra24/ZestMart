from flask import Blueprint, current_app

from controllers.auth_controller import (
    get_session,
    login_staff,
    login_student,
    logout,
    register_student,
    send_otp,
    verify_otp,
)
from extensions import limiter


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

auth_bp.post("/send-otp")(limiter.limit(lambda: current_app.config["OTP_SEND_RATE_LIMIT"])(send_otp))
auth_bp.post("/verify-otp")(limiter.limit(lambda: current_app.config["OTP_VERIFY_RATE_LIMIT"])(verify_otp))
auth_bp.post("/register")(register_student)
auth_bp.post("/login/student")(limiter.limit(lambda: current_app.config["LOGIN_RATE_LIMIT"])(login_student))
auth_bp.post("/login/staff")(limiter.limit(lambda: current_app.config["LOGIN_RATE_LIMIT"])(login_staff))
auth_bp.get("/session")(get_session)
auth_bp.post("/logout")(logout)
