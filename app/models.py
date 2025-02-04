from flask import current_app
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


# Определение модели Role
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    # Атрибут users это объектно-ориентированное представление отношения.
    # При обращении к атрибуту users будет возвращаться список
    # пользователей с данной ролью.

    # Аргумент backref определяет обратную ссылку отношения –
    # атрибут role в модели User.
    # Данный атрибут можно использовать вместо role_id для доступа
    # к модели Role как к объекту.
    # Присовение атрибуту lazy='dynamic' означает возврат не самих
    # элементов - пользователей, а ЗАПРОС для возврата этих элементов.
    # Это делается для применения дополнительных фильтров/сортировок
    # вида role_user.users.order_by(User.username).all().
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


# UserMixin - для поддержки методов аутентификации: is_authenticated, is_active и проч.
class User(db.Model, UserMixin):
    __tablename__ = 'users'     # Имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    # Внешний ключ для отношения с таблицей roles
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=2)

    # @property позволяет определять метод класса как свойство и доступ к нему
    # осуществлять как к обычному атрибуту.
    @property
    def password(self):     # Геттер
        """Защита чтения пароля напрямую.
        При попытке обратиться к user.password будет выброшено исключение."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):   # Сеттер
        """Установка пароля и автоматическое сохранение его в виде хэша."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Проверка хэша пароля."""
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        """Генерация подписанного токена для подтверждения email."""

        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}, salt='email-confirm-salt')

    def confirm(self, token, expiration=3600):
        """Метод подтверждения токена.
        Если удачно - сделает атрибут confirmed = 1 и вернет True.
        """
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='email-confirm-salt', max_age=expiration)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя по ID.
    Требование Flask-Login."""
    return User.query.get(int(user_id))


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return f'<User {self.id}>'
