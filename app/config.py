import os
from pathlib import Path

# if not os.getenv('SPHINX_BUILD'):
from dotenv import load_dotenv

load_dotenv()

basedir = Path(__file__).resolve().parent


class Config:

    @property
    def SECRET_KEY(self):
        return os.getenv('SECRET_KEY')

    @property
    def MAIL_USERNAME(self):
        return os.getenv('MAIL_USERNAME')

    @property
    def MAIL_PASSWORD(self):
        return os.getenv('MAIL_PASSWORD')

    @property
    def MAIL_SERVER(self):
        return os.getenv('MAIL_SERVER')

    @property
    def MAIL_PORT(self):
        return os.getenv('MAIL_PORT')

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Отключение перехвата редиректов в режиме debug
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # При импорте логических переменных важно ЯВНО привести их к логическому
    # типу. Иначе они будут интерпретированы как строка, что в свою очередь
    # приведет к ошибкам (любая строка всегда `True`).
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False') == 'True'  # В бул.
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    MAIL_SUBJECT_PREFIX = '[Big Project]'
    MAIL_SENDER = os.getenv('MAIL_SENDER')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir / "instance/data.sqlite"}'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{basedir / "instance/data-test.sqlite"}'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,

    'default': DevelopmentConfig
}
