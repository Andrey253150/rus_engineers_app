"""Этот модуль определяет обработчики ошибок HTTP для всего приложения.

Функции:
    - page_not_found(e): Обрабатывает ошибку 404.
    - internal_server_error(e): Обрабатывает ошибку 500.
    - forbidden(e): Обрабатывает ошибку 403.
    - unauthorized(e): Обрабатывает ошибку 401.
"""
from flask import current_app, render_template


def page_not_found(e) -> tuple:
    """Обрабатывает ошибку 404 (Страница не найдена).
    """
    current_app.logger.warning(f"Ошибка 404: {e}")
    return render_template('error.html', code=404, message="Страница не найдена"), 404


def internal_server_error(e) -> tuple:
    """Обрабатывает ошибку 500 (Внутренняя ошибка сервера).
    """
    current_app.logger.error(f"Ошибка 500: {e}", exc_info=True)
    return render_template('error.html', code=500, message="Внутренняя ошибка сервера"), 500


def forbidden(e):
    """
    Обрабатывает ошибку 403 (пользователь не имеет доступа).
    """
    current_app.logger.warning(f"Ошибка 403: {e}")
    return render_template('error.html', code=403, message="Доступ запрещён"), 403


def unauthorized(e):
    """
    Обрабатывает ошибку 401 (пользователь не авторизован).
    """
    current_app.logger.warning(f"Ошибка 401: {e}")
    return render_template('error.html', code=401, message="Необходима авторизация"), 401


def register_error_handlers(app):
    """Регистрирует обработчики ошибок во Flask-приложении."""
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(401, unauthorized)
