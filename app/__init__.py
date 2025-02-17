"""
Главный модуль приложения.

Шаг 1.
Создание объектов-расширений без инициализации приложения.

Шаг 2.
Фабричная функция create_app(), внутри которой:
 - создается экземпляр приложения и загр. нужная конф-ия (config_name);
 - инициализируются объекты-расширения;
 - регистрируются макеты;
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

from .config import config

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

    app.config.from_object(config[config_name])

    toolbar.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Рег. макетов
    from .main import main_bp
    app.register_blueprint(main_bp)

    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
