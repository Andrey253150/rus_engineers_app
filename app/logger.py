"""Настройка логирования для приложения.

Этот модуль конфигурирует логирование, включая:
    - Создание именованного логгера.
    - Настройку формата сообщений.
    - Добавление обработчика для вывода логов в консоль.

Логгер записывает сообщения уровня INFO и выше.
"""

import logging


def setup_logger() -> logging.Logger:
    """Создаёт и настраивает логгер для приложения.

    Возвращает:
        logging.Logger: Настроенный логгер.
    """
    logger = logging.getLogger("my_app")
    logger.setLevel(logging.INFO)

    # Определение формата логирования
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Создание обработчика для вывода в консоль
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


# Инициализация логгера
logger = setup_logger()
