"""Модуль с утилитами и расширениями.
Здесь можно хранить контекстные процессоры.
"""


def inject_permissions():
    from .models import Permission
    return dict(Permission=Permission)
