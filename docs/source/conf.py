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

templates_path = ['_templates']
exclude_patterns = []

language = 'ru'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'    # furo, sphinx_rtd_theme
html_static_path = ['_static']
html_css_files = ['custom.css']
html_favicon = '_static/favicon.ico'
