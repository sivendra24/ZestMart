from flask import current_app, g, make_response, request

from middleware.auth_middleware import auth_required
from services.auth_service import auth_service
from utils.jwt_helper import clear_auth_cookie, set_auth_cookie
from utils.response_helper import success_response


def _auth_success_response(message, result, status_code=200):
    response = make_response(*success_response(message, {"user": result["user"]}, status_code))
    set_auth_cookie(response, result["sessionToken"], current_app.config)
    return response


def send_otp():
    payload = request.get_json(silent=True) or {}
    result = auth_service.send_otp(payload)
    return success_response("OTP generated successfully.", result, 201)


def verify_otp():
    payload = request.get_json(silent=True) or {}
    result = auth_service.verify_otp(payload)
    return success_response("OTP verified successfully.", result)


def register_student():
    payload = request.get_json(silent=True) or {}
    result = auth_service.register_student(payload)
    return _auth_success_response("Student registration completed successfully.", result, 201)


def login_student():
    payload = request.get_json(silent=True) or {}
    result = auth_service.login_student(payload)
    return _auth_success_response("Student login successful.", result)


def login_staff():
    payload = request.get_json(silent=True) or {}
    result = auth_service.login_staff(payload)
    return _auth_success_response("Staff login successful.", result)


@auth_required
def get_session():
    return success_response("Active session fetched successfully.", {"user": g.current_user})


def logout():
    response = make_response(*success_response("Signed out successfully.", {}))
    clear_auth_cookie(response, current_app.config)
    return response
