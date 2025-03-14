import os
import sys

import click
import pytest

from app import create_app

app = create_app()


# Регистрация команды 'test' в flask-cli
@app.cli.command("test")
@click.option("--test-file", default=None, help="Запуск конкретного тестового файла")
def run_tests(test_file):
    """
    Запуск тестов через flask test с возможностью
    запустить конкретный файл из папки tests/.
    Пример запуска:
        1) flask test (все тесты)
        2) flask test --test-file test_user_model.py (без указания директории)
    """

    # Определяем путь к тестам
    test_path = "tests"

    # Если указан конкретный файл, добавляем его к пути
    if test_file:
        test_path = os.path.join(test_path, test_file)

    # Аргументы для pytest
    pytest_args = [
        test_path,  # Путь к тестам
        "-v",       # Подробный вывод
        "--cov=app",  # Включение покрытия кода (опционально)
    ]

    # Запуск pytest
    exit_code = pytest.main(pytest_args)

    # Завершение с соответствующим кодом
    sys.exit(exit_code)


if __name__ == "__main__":
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(host=host, port=port)


# import os
# import unittest

# import click

# from app import create_app

# app = create_app()


# # Регистрация команды 'test' в flask-cli
# @app.cli.command("test")
# # Функциональность для запуска конкретного тест-файла
# @click.option("--test-file", default=None, help="Запуск конкретного тестового файла")
# def run_tests(test_file):
#     """
#     Запуск тестов через flask test с возможностью
#     запустить конкретный файл из папки tests/.
#     Пример запуска:
#         2) flask test (все тесты)
#         1) flask test --test-file test_user_model.py (без указания директории)
#     """

#     # TestLoader - ищет и загружает все тесты из директории tests
#     # discover - рекурсивно находит все тестовые файлы (test*.py и *test.py)
#     if test_file:
#         tests = unittest.TestLoader().discover('tests', pattern=test_file)
#     else:
#         tests = unittest.TestLoader().discover('tests')

#     # Выполнение тестов
#     result = unittest.TextTestRunner(verbosity=2).run(tests)
#     if result.wasSuccessful():
#         exit(0)     # Код 0 - завершить с успехом
#     exit(1)         # Код  - завершить с ошибкой


# if __name__ == "__main__":
#     host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
#     port = int(os.getenv('FLASK_RUN_PORT', 5000))
#     app.run(host=host, port=port)

