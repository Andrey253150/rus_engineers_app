"""Этот модуль определяет обработчики ошибок HTTP для всего приложения."""

from flask import current_app, jsonify, make_response, render_template, request


def generate_error_response(status_code, error_message):
    """
    Формирует ответ с ошибкой в зависимости от типа запроса (API или веб).

    Если запрос направлен к API (определяется по началу пути `/api`),
    возвращается JSON-ответ с указанным статус-кодом и сообщением об ошибке.
    Для остальных запросов возвращается HTML-страница с шаблоном ошибки.

    Аргументы:
        status_code (int): HTTP-код ошибки (например, 404, 403).
        error_message (str): Текстовое описание ошибки.

    Возвращает:
        Response: Объект ответа Flask. Тип ответа зависит от запроса: JSON для API или HTML для веба.
    """
    # if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
    if request.path.startswith('/api'):
        response = make_response(jsonify(
            {
                'status': 'error',
                'code': status_code,
                'error': error_message
            }
        ), status_code)
        return response
    return render_template('error.html', code=status_code, message=error_message), status_code


def generate_custom_error_message(current_msg, flask_default_msg, custom_msg):
    custom_msg = custom_msg
    message = str(current_msg).strip()
    if not message or message.startswith(flask_default_msg):
        message = custom_msg

    return message


def unauthorized(e) -> tuple:
    """Обрабатывает ошибку 401 (пользователь не авторизован)."""

    current_app.logger.warning(f"{e}")
    return generate_error_response(401, "Неверное имя пользователя или пароль.")


def forbidden(e) -> tuple:
    """Обрабатывает ошибку 403 (пользователь не имеет доступа)."""

    message = generate_custom_error_message(
        e.description,
        "You don't have the permission",
        "Доступ запрещён: у пользователя нет прав на данное действие."
    )

    current_app.logger.warning(f"{e}")
    return generate_error_response(e.code, message)


def page_not_found(e) -> tuple:
    """Обрабатывает ошибку 404 (Страница не найдена)."""

    message = generate_custom_error_message(
        e.description,
        "The requested URL was not found on the server",
        "Страница не найдена, дядь"
    )

    current_app.logger.warning(f"{e}")
    return generate_error_response(e.code, message)


def internal_server_error(e) -> tuple:
    """Обрабатывает ошибку 500 (Внутренняя ошибка сервера)."""

    current_app.logger.warning(f"{e}")
    return generate_error_response(500, "Внутренняя ошибка сервера")


def register_error_handlers(app):
    """Регистрирует обработчики ошибок во Flask-приложении."""

    app.register_error_handler(401, unauthorized)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)
