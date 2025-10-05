from functools import wraps
from flask import redirect, session, url_for, request, abort

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def check_csrf():
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)