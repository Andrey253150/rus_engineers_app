from datetime import datetime, timezone

from flask import current_app
from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous import URLSafeTimedSerializer
from itsdangerous.exc import BadSignature, SignatureExpired
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


class Permission:
    FOLLOW = 0x01               # Разрешается следовать за другими пользователями
    COMMENT = 0x02              # Разрешается комментировать статьи, написанные другими пользователями
    WRITE_ARTICLES = 0x04       # Разрешается писать собственные статьи
    MODERATE_COMMENTS = 0x08    # Разрешается подавлять оскорбительные комменты других пользователей
    ADMINISTER = 0x80           # Административный доступ к сайту


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

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
        return f'Role(id = {self.id}, name = {self.name})'

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = db.session.scalar(select(Role).where(Role.name == r))

            # Если такой роли нет - заводим новую роль
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


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

    posts = db.relationship('Post', backref='author', lazy='dynamic')

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.now(timezone.utc))

    # Нужно постоянно обновлять, для этого сделан отдельный метод ping
    last_seen = db.Column(db.DateTime(), default=datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        """Инициализирует объект пользователя и назначает роль администратора, если email совпадает
        с email администратора.

        При создании пользователя:
        - super().__init__(**kwargs) вызывает конструктор db.Model, который инициализирует
            атрибуты, определенные через db.Column.
        - Если email пользователя совпадает с email администратора (указанным в конфигурации приложения),
        пользователю назначается роль администратора.
        - Если email не совпадает, пользователю автоматически назначается роль по умолчанию (благодаря
            `default=2` в `role_id`).

        Args:
            **kwargs: Произвольные именованные аргументы, передаваемые в родительский конструктор.
                    Обычно включают `email`, `username`, и другие атрибуты пользователя.

        Example:
            >>> user = User(email='user@example.com', username='user')
            >>> user.role_id  # Роль по умолчанию (например, 2 для "User")
            2

            >>> admin = User(email='admin@example.com', username='admin')
            >>> admin.role_id  # Роль администратора (например, 1 для "Administrator")
            1
        """
        super().__init__(**kwargs)
        if self.email == current_app.config['ADMIN_EMAIL']:
            stmt = select(Role).where(Role.permissions == 0xff)
            self.role = db.session.scalar(stmt).one()

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

    def can(self, permissions):
        """
        Проверяет, есть ли у пользователя (или объекта) все необходимые разрешения.

        Метод выполняет битовую операцию AND для текущих разрешений пользователя и переданных разрешений.
        Если у пользователя есть все необходимые разрешения, метод возвращает True.
        В противном случае — False.

        Args:
            permissions (int): Разрешения, которые нужно проверить. Представляются в виде целого числа,
                                где каждый бит отвечает за отдельное разрешение.

        Returns:
            bool: True, если у пользователя есть все переданные разрешения, иначе False.

        Example:
            >>> user = User(role=Role(permissions=3))  # У пользователя есть разрешения на чтение и запись
            >>> user.can(2)  # Проверка разрешения на запись
            True

            >>> user.can(4)  # Проверка разрешения на выполнение
            False
        """
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.now(timezone.utc)
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return f'User (id = {self.id}, username = {self.username}, email = {self.email})'


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# Установка собственного класса для анонимного пользователя
login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя по ID.
    Требование Flask-Login."""
    return User.query.get(int(user_id))




