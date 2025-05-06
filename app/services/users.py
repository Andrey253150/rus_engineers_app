"""Это место для бизнес-логики и сервисных функций, таких как создание пользователя.
Такой подход позволит тебе отделить логику работы с данными от самой модели.
"""

from app.models import Role, User, db


def create_user(session=None, **kwargs):
    if session is None:
        session = db.session  # используется по умолчанию, если не передали явно
    user = User(**kwargs)
    if user.role is None:
        # Пробуем найти роль по умолчанию
        # user.role = session.query(Role).filter_by(name='User').first()
        user.role = session.scalar(db.select(Role).where(Role.name == 'User'))
    db.session.add(user)
    db.session.flush()
    user.add_self_follow()
    # db.session.commit()
    return user
