from functools import wraps

from flask import abort
from flask_login import current_user

from .models import Permission


def permission_required(permission):        # Внешняя функция — принимает аргументы декоратора.
    def decorator(f):                       # Средняя функция — принимает функцию, которую нужно декорировать.
        @wraps(f)
        def wrapper(*args, **kwargs):       # Внутренняя функция — добавляет новое поведение.
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)
