"""
Главный модуль приложения.

Шаги инициализации:

1. Создание объектов-расширений без инициализации приложения.

2. Фабричная функция `create_app()`, внутри которой:

   - создается экземпляр приложения и загружается нужная конфигурация (`config_name`);
   - инициализируются объекты-расширения;
   - регистрируются макеты, фильтры, контекстные процессоры;
   - возвращается настроенный экземпляр приложения.
"""

import os

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .config import config
from .errors import register_error_handlers
from .filters import log_class
from .logger import setup_logger
from .utils import inject_permissions

toolbar = DebugToolbarExtension()
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
migrate = Migrate()

# Инициализация Flask-Login и настройка
login_manager = LoginManager()
login_manager.session_protection = 'strong'    # Уровень защиты сеанса (по умолч. basic)
login_manager.login_view = 'auth.login'        # Маршрут для неавторизованных польз.


# Подключение поддержки внешних ключей для SQLite
@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # Только для SQLite
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'default')

    if config_name not in config:
        config_name = 'default'  # Устанавливаем значение по умолчанию
        print(f"""
Указан недопустимый вариант конфигурации.
Досутпные варианты конфигураций: {list(config.keys())}.
Приложение будет запущено в режиме \
по умолчанию).
""")
    # Передаем экземпляр, чтобы @property в config.py сработало
    app.config.from_object(config[config_name]())

    setup_logger(app)

    toolbar.init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Рег. макетов приложения
    from .main import main_bp
    app.register_blueprint(main_bp)

    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    # Рег. api
    from .api.v1 import api_v1_bp
    app.register_blueprint(api_v1_bp)

    register_error_handlers(app)

    # Регистрируем фильтр Jinja2
    app.jinja_env.filters["log_class"] = log_class

    # Регистрация контекстного процессора
    app.context_processor(inject_permissions)

    return app
