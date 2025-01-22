from . import db


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


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    # Внешний ключ для отношения с таблицей roles
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=2)

    def __repr__(self):
        return f'<User {self.username}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f'<User {self.id}>'
