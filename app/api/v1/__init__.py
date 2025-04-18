from flask import Blueprint
from marshmallow import ValidationError

from .errors import bad_request_error, validation_error

api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

# Для ошибок валидации
api_v1_bp.register_error_handler(ValidationError, validation_error)

# Для прочих 400 ошибок
api_v1_bp.register_error_handler(400, bad_request_error)

from . import resources  # Импорт маршрутов
