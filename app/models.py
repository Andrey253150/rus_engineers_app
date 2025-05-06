from datetime import datetime, timezone
from random import randint

import mistune  # Markdown-парсер
from faker import Faker
from flask import abort, current_app, url_for
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

    # Присовение атрибуту lazy='dynamic' означает возврат не самих
    # элементов - пользователей, а ЗАПРОС для возврата этих элементов.
    # Это делается для применения дополнительных фильтров/сортировок
    # вида role_user.users.order_by(User.username).all().
    users = db.relationship('User',
                            back_populates='role')  # lazy='dynamic'

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


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer,
                            db.ForeignKey('users.id', ondelete='CASCADE'),
                            primary_key=True)

    follower = db.relationship('User',
                               foreign_keys=[follower_id],
                               back_populates='followed',
                               # Нужна одна жадная загрузка вместо кучи маленьких (проблема N+1).
                               # В режиме lazy='joined' связанные объекты извлекаются немедленно из
                               # запроса соединения.
                               lazy='joined')

    followed_id = db.Column(db.Integer,
                            db.ForeignKey('users.id', ondelete='CASCADE'),
                            primary_key=True)

    followed = db.relationship('User',
                               foreign_keys=[followed_id],
                               back_populates='followers',
                               # Нужна одна жадная загрузка вместо кучи маленьких (проблема N+1).
                               # В режиме lazy='joined' связанные объекты извлекаются немедленно из
                               # запроса соединения.
                               lazy='joined')

    timestamp = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Follow(followed_id = {self.followed_id}, follower_id = {self.follower_id})>'


# UserMixin - для поддержки методов аутентификации: is_authenticated, is_active и проч.
class User(db.Model, UserMixin):
    __tablename__ = 'users'     # Имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.now(timezone.utc))

    # Нужно постоянно обновлять, для этого сделан отдельный метод ping
    last_seen = db.Column(db.DateTime(), default=datetime.now(timezone.utc))

    posts = db.relationship('Post',
                            back_populates='author',
                            lazy='dynamic',
                            cascade='all, delete-orphan',
                            passive_deletes=True)

    role_id = db.Column(db.Integer,
                        db.ForeignKey('roles.id', ondelete='SET NULL'),
                        # default=1,  # Роль по умолчанию лучше присваивать в фабрике create_user
                        nullable=True
                        )

    role = db.relationship('Role',
                           back_populates='users')

    # Набор подписчиков - это строки модели follows, связанные по нужному значению followed_id
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                back_populates='followed',
                                lazy='dynamic',
                                cascade='all, delete-orphan',
                                passive_deletes=True)

    # Набор подписок - это строки модели follows, связанные по нужному значению follower_id
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               back_populates='follower',
                               lazy='dynamic',
                               cascade='all, delete-orphan',
                               passive_deletes=True)

    comments = db.relationship('Comment',
                               back_populates='author',
                               lazy='dynamic',
                               cascade='all, delete-orphan',
                               passive_deletes=True)

    def to_json(self):
        json_user = {
            'url': url_for('api_v1.get_user_profile', username=self.username, _external=True),
            'username': self.username,
            'name': self.name,
            'about_me': self.about_me,
            'location': self.location,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'following_list': [follows.followed.username for follows in self.followed],
            'following_count': self.followed.count() - 1,
            'followers_list': [follows.follower.username for follows in self.followers],
            'followers_count': self.followers.count() - 1,
            'posts': url_for('api_v1.get_user_posts', username=self.username, _external=True),
            'feed': url_for('api_v1.get_user_feed', username=self.username, _external=True),
            'posts_count': self.posts.count(),
            'comments_count': self.comments.count()
        }

        return json_user

    def generate_auth_token(self, expiration=216000):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'], expiration)
        token = s.dumps({'id': self.id}, salt='auth-token-salt')
        return token

    @staticmethod
    def verify_auth_token(token, expiration=216000):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='auth-token-salt', max_age=expiration)
        except (BadSignature, SignatureExpired):
            return None

        return db.session.get(User, data['id'])

    @property
    def feed_posts(self):
        stmt = (select(Post).join(Follow, Post.author_id == Follow.followed_id).
                where(Follow.follower_id == self.id).
                order_by(Post.timestamp.desc()))
        return stmt

    def __init__(self, **kwargs):
        """Инициализирует объект пользователя и назначает роль администратора, если email совпадает
        с email администратора.

        При создании пользователя:
        - super().__init__(**kwargs) вызывает конструктор db.Model, который инициализирует
            атрибуты, определенные через db.Column.
        - Если email пользователя совпадает с email администратора (указанным в конфигурации приложения),
        пользователю назначается роль администратора.
        - Если email не совпадает, пользователю автоматически назначается роль по умолчанию (благодаря
            `default=1` в `role_id`).

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

        # self.follow(self)   # Подписаться на самого себя (для отображения своих сообщений в ленте)

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        """Удаление подписки на пользователя.
        Что происходит: удаляется запись из таблицы follows (т.е. удаляется Follow-объект).
        Доступ к записям осуществляется через self.followed .
        """
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
            db.session.commit()

    @staticmethod
    def generate_fake(count=10):
        fake = Faker('ru_Ru')
        users = []
        for _ in range(count):
            user = User(
                username=fake.unique.user_name(),
                name=f"{fake.first_name()} {fake.last_name()}",
                email=fake.unique.email(),
                password=generate_password_hash(fake.password(length=12)),
                confirmed=True,
                location=fake.city(),
                about_me=fake.text(max_nb_chars=200),
                member_since=fake.date_time_between(
                    start_date='-2y',
                    end_date='now'))
            db.session.add(user)
            users.append(user)
        try:
            db.session.flush()  # Получаем id, но не коммитим
            for user in users:
                user.add_self_follow()  # Пользователи подписываются на себя
            db.session.commit()
            return users
        except Exception as e:
            db.session.rollback()
            raise e

    def add_self_follow(self):
        """Метод для подписки создаваемого пользователя на самого себя."""
        if not self.is_following(self):
            f = Follow(follower=self, followed=self)
            db.session.add(f)

    @staticmethod
    def add_self_follows():
        """Регистрация существующих пользователей
        как читающих самих себя.
        """
        for user in db.session.scalars(select(User)).all():
            user.add_self_follow()
        db.session.commit()

    # @property определяет метод класса как свойство с доступом как к обычному атрибуту.
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


# Установка собственного класса для анонимного пользователя
login_manager.anonymous_user = AnonymousUser


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))

    author_id = db.Column(db.Integer,
                          db.ForeignKey('users.id', ondelete='CASCADE'))

    # Если объект Post теряет связь с User (т.е. больше не привязан ни к какому автору), он будет удалён из БД автоматически.
    author = db.relationship('User',
                             back_populates='posts')

    comments = db.relationship('Comment',
                               back_populates='post',
                               lazy='dynamic',
                               cascade='all, delete-orphan',
                               passive_deletes=True)

    def to_json(self, include_disabled_comments=False, only_few_comments=False):
        """
        Сериализует объект поста в словарь, пригодный для преобразования в JSON.

        Включает основную информацию о посте, а также связанные комментарии.
        Поддерживает опции для включения отключённых комментариев и сокращённого режима отображения.

        Аргументы:
            include_disabled_comments (bool): Если True — включает в вывод отключённые комментарии.
                Если False — исключает их. По умолчанию False.
            only_few_comments (bool): Если True — возвращаются только первые три комментария (после фильтрации).
                Полезно для превью. По умолчанию False.

        Возвращает:
            dict: Словарь, содержащий сериализованные данные поста:
                - 'url' (str): Абсолютный URL поста.
                - 'body' (str): Текст поста.
                - 'timestamp' (datetime): Дата и время создания поста.
                - 'author' (str): URL профиля автора.
                - 'comments' (list): Список сериализованных комментариев.
                - 'comments_count (including disabled)' (int): Общее количество комментариев, включая отключённые.
    """
        json_post = {
            'url': url_for('api_v1.get_post', id=self.id, _external=True),
            'body': self.body,
            'timestamp': self.timestamp,
            'author': url_for('api_v1.get_user_profile', username=self.author.username, _external=True),
            'comments': [],
            'comments_count (including disabled)': self.comments.count()
        }

        if include_disabled_comments:
            # Отключаем показ заблокированных комментов
            comments = self.comments.all()
        else:
            comments = self.comments.filter(
                # (Comment.disabled.is_(False)) | (Comment.disabled.is_(None))
                Comment.disabled.isnot(True)
            ).all()

        if only_few_comments:
            # Показать тольк опервые 3 коммента
            comments = comments[:3]

        json_post['comments'] = [comment.to_json(include_post_info=False) for comment in comments]

        return json_post

    @staticmethod
    def from_json(json_post: dict) -> 'Post':
        """Создаёт объект Post из JSON-данных с валидацией.

        Принимает словарь с данными поста, проверяет обязательные поля
        и возвращает новый экземпляр класса Post.

        Args:
            json_post (dict):
                Словарь с данными поста. Обязательные поля:
                - 'body' (str): Текст поста. Не может быть пустым.

        Returns:
            Post: Новый экземпляр класса Post с заполненным полем `body`.

        Raises:
            ValidationError:
                - Если поле 'body' отсутствует в json_post.
                - Если 'body' пустая строка.

        Examples:
            #### Успешное создание поста
            ```python
            data = {'body': 'Hello, world!'}
            post = Post.from_json(data)
            ```

            #### Невалидные данные (вызовут исключение)
            ```python
            Post.from_json({})  # Нет поля 'body'
            Post.from_json({'body': ''})  # Пустой 'body'
            ```
        """

        body = json_post.get('body')
        if body is None or body == '':
            # raise ValidationError('post does not have a body')
            abort(400)

        return Post(body=body)

    # 🔹 Метод для рендеринга Markdown → HTML
    def render_html(self):
        return mistune.markdown(self.body)

    @staticmethod
    def generate_fake(count=10, author_ids=None):
        fake = Faker('ru_Ru')
        if author_ids is None:
            author_ids = db.session.scalars(db.select(User.id)).all()
            if not author_ids:
                raise ValueError("В базе нет пользователей. Сначала создайте авторов!")
        new_posts = []
        for i in range(count):
            post = Post(
                body=fake.text(max_nb_chars=1000),
                timestamp=fake.date_time_between(
                    start_date='-2y',
                    end_date='now'),
                author_id=author_ids[randint(0, len(author_ids) - 1)]
            )
            new_posts.append(post)
        db.session.add_all(new_posts)
        db.session.commit()

        return new_posts


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.now(timezone.utc))
    disabled = db.Column(db.Boolean)

    author_id = db.Column(db.Integer,
                          db.ForeignKey('users.id', ondelete='CASCADE'))

    author = db.relationship('User',
                             back_populates='comments')

    post_id = db.Column(db.Integer,
                        db.ForeignKey('posts.id', ondelete='CASCADE'))

    post = db.relationship('Post',
                           back_populates='comments')

    def to_json(self, include_post_info=True):
        json_comment = {
            'url': url_for('api_v1.get_comment', id=self.id, _external=True),
            'body': self.body,
            'created_at': self.created_at,
            'author': url_for('api_v1.get_user_profile', username=self.author.username, _external=True)
        }

        if include_post_info:
            # Опционально добавляем инфо о посте
            json_comment['post_url'] = url_for('api_v1.get_post', id=self.post_id, _external=True)
            json_comment['post'] = self.post.body[:40]

        return json_comment


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя по ID.
    Требование Flask-Login."""
    return db.session.get(User, int(user_id))
