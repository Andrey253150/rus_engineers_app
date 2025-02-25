"""
Модуль аутентификации приложения.

Доступные подмодули:

1. Формы

2. Представления:

   - для одного;
   - другого;
   - третьего.
"""
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import views
