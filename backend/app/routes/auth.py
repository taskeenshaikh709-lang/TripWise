import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def public_user(user):
    return {"id": user.id, "name": user.name, "email": user.email}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(status="error", message="A JSON request body is required."), 400

    name = data.get("name", "").strip() if isinstance(data.get("name"), str) else ""
    email = data.get("email", "").strip().lower() if isinstance(data.get("email"), str) else ""
    password = data.get("password") if isinstance(data.get("password"), str) else ""
    if not name or len(name) > 100:
        return jsonify(status="error", message="Enter a name of up to 100 characters."), 400
    if not EMAIL_PATTERN.fullmatch(email):
        return jsonify(status="error", message="Enter a valid email address."), 400
    if len(password) < 8 or len(password) > 128:
        return jsonify(status="error", message="Password must contain 8 to 128 characters."), 400
    if User.query.filter_by(email=email).first():
        return jsonify(status="error", message="That email address is already registered."), 409

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(status="error", message="That email address is already registered."), 409

    return jsonify(
        status="success",
        message="Your account is ready.",
        user=public_user(user),
        access_token=create_access_token(identity=str(user.id)),
    ), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)
    email = data.get("email", "").strip().lower() if isinstance(data, dict) and isinstance(data.get("email"), str) else ""
    password = data.get("password", "") if isinstance(data, dict) and isinstance(data.get("password"), str) else ""
    user = User.query.filter_by(email=email).first() if email else None
    if not user or not user.check_password(password):
        return jsonify(status="error", message="Email or password is incorrect."), 401
    return jsonify(
        status="success",
        user=public_user(user),
        access_token=create_access_token(identity=str(user.id)),
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        return jsonify(status="error", message="This account no longer exists."), 404
    return jsonify(status="success", user=public_user(user))
