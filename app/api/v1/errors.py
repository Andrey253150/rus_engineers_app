from flask import current_app

from app.errors import generate_error_response


def validation_error(e):
    current_app.logger.warning(f"Ошибка ValidationError: {e}")
    error_message = e.description if isinstance(e.description, str) else "Ошибка валидации"
    return generate_error_response(400, error_message)


def bad_request_error(e):
    current_app.logger.warning(f"Ошибка 400 (не ValidationError): {e}")
    error_message = e.description if isinstance(e.description, str) else "Ошибка 400 (не ValidationError)"
    return generate_error_response(400, error_message)
