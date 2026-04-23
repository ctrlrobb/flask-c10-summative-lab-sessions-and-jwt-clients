from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

try:
    from ..models import User, db
except ImportError:
    from models import User, db

from .helpers import error_response, get_current_user, login_required


class SignupResource(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        password_confirmation = data.get("password_confirmation")

        if password != password_confirmation:
            return error_response("Password confirmation must match password.", 422)

        try:
            user = User(username=username)
            user.password = password
            db.session.add(user)
            db.session.commit()
        except ValueError as exc:
            db.session.rollback()
            return error_response(str(exc), 422)
        except IntegrityError:
            db.session.rollback()
            return error_response("Username has already been taken.", 422)

        session["user_id"] = user.id
        return user.public_dict(), 201


class LoginResource(Resource):
    def post(self):
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        user = User.query.filter_by(username=username).first()
        if user is None or not user.authenticate(password):
            return error_response("Invalid username or password.", 401)

        session["user_id"] = user.id
        return user.public_dict(), 200


class CheckSessionResource(Resource):
    def get(self):
        user = get_current_user()
        if user is None:
            return {}, 401
        return user.public_dict(), 200


class LogoutResource(Resource):
    @login_required
    def delete(self, current_user=None):
        session.pop("user_id", None)
        return {}, 200
