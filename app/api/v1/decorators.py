from functools import wraps

from flask import g

from app.errors import forbidden


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Нехватает прав')
            return f(*args, **kwargs)

        return wrapper
    return decorator
