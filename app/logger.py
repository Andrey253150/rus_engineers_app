"""
Модуль логирования для Flask-приложения.

Этот модуль настраивает логирование в приложении Flask, включая:
- Вывод логов в консоль.
- Запись логов в файл.
- Автоматическое создание директории и файла логов.
- Очистку существующих обработчиков для предотвращения дублирования.

Пример использования:
    from flask import Flask
    from logger import setup_logger

    app = Flask(__name__)
    setup_logger(app)
    app.logger.info("Приложение запущено.")
"""

import logging
import os

from flask import Flask

LOG_FILE = "logs/app.log"


def setup_logger(app: Flask):
    """Настраивает логирование для Flask-приложения.

    Функция выполняет следующие действия:
    1. Устанавливает уровень логирования на INFO.
    2. Отключает распространение логов, чтобы избежать дублирования.
    3. Создаёт папку и файл логов, если они не существуют.
    4. Очищает существующие обработчики логирования.
    5. Добавляет обработчик для вывода логов в консоль.
    6. Добавляет обработчик для записи логов в файл.

    Args:
        app (Flask): Flask-приложение, для которого настраивается логирование.

    Raises:
        Exception: В случае ошибки при настройке логирования.
    """
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False  # Отключаем распространение логов

    try:
        if not os.path.exists("logs"):
            os.makedirs("logs")  # Создаём папку для логов, если её нет

        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")  # Создаём пустой файл, если его нет
        
        # Очищаем логгер от всех хэндлеров.
        app.logger.handlers.clear()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Обработчик для вывода в консоль
        std_handler = logging.StreamHandler()
        std_handler.setFormatter(formatter)
        app.logger.addHandler(std_handler)

        # Обработчик для записи в файл
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        # file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.info("Логирование успешно настроено.")

    except Exception as e:
        print(f"Ошибка при настройке логирования: {e}")
