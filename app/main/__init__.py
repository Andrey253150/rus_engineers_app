
"""
Модуль макета (blueprint) main.

Создание макета (blueprint) и привязввание к нему через импорт
функций представлений В КОНЦЕ ФАЙЛА во избежание
циклических ссылок, потому что views/errors сами импортируют макет.

Связвание в __init__.py происходит автоматически.
Этот файл служит точкой входа для подключения всей логики Blueprint.
"""
from flask import Blueprint

main_bp = Blueprint('main', __name__)

from . import errors, views
