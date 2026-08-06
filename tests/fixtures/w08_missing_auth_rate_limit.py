from flask import Blueprint, request, jsonify

bp = Blueprint("auth", __name__)


@bp.post("/login")
def login():
    email = request.json["email"]
    password = request.json["password"]
    user = users.find_by_email(email)
    if user and verify(user.password_hash, password):
        return jsonify(token=issue_token(user))
    return jsonify(error="invalid credentials"), 401


@bp.post("/password-reset/verify-otp")
def verify_otp():
    return jsonify(ok=otp_store.check(request.json["email"], request.json["otp"]))
