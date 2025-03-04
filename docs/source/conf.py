# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('../../'))  # Укажите путь к корню проекта
from app import create_app

app = create_app()

project = 'Russian Engineers'
copyright = '2025, Andrey Solomatin'
author = 'Andrey Solomatin'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
if app:
    with app.app_context():
        extensions = [
            'sphinx.ext.autodoc',   # Автоматическое документирование
            'sphinx.ext.viewcode',  # Добавляет ссылки на исходный код
            'sphinx.ext.napoleon',  # Поддержка Google- и NumPy-стиля документации
            'sphinx_rtd_theme',     # Тема Read the Docs
        ]

# templates_path = ['templates']
exclude_patterns = ['.env', 'venv', 'env']

language = 'ru'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'    # furo, sphinx_rtd_theme, python_docs_theme, alabaster, sphinx_book_theme
html_static_path = ['static']
html_css_files = ['custom.css']
html_favicon = 'static/favicon.ico'

html_theme_options = {
    # 'toc_depth': 4,  # Глубина вложенности меню
}


# autodoc_default_options = {
#     'exclude-members': 'SECRET_KEY, MAIL_PASSWORD',  # Исключаем переменные окружения
# }
