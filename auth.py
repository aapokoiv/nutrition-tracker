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
    token = request.form.get("csrf_token")
    if not token or token != session.get("csrf_token"):
        abort(403)
