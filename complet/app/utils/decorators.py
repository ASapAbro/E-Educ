from functools import wraps

from flask import abort
from flask_login import current_user


def roles_required(*roles):
    """Restrict a route to the given roles. Must be used with @login_required."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
