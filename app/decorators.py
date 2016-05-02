from functools import wraps
from flask import abort
from flask_login import current_user

#mostly taken from Flask-User

def roles_accepted(*role_names):
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if not current_user.has_role(*role_names):
                abort(403)

            return func(*args, **kwargs)
        return decorated_view
    return wrapper
