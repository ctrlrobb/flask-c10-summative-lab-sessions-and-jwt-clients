from functools import wraps

from flask import session

try:
    from ..models import User, db
except ImportError:
    from models import User, db


def error_response(errors, status_code):
    if isinstance(errors, str):
        errors = [errors]
    return {"errors": errors}, status_code


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if user is None:
            return error_response("Unauthorized", 401)
        return fn(*args, current_user=user, **kwargs)

    return wrapper
