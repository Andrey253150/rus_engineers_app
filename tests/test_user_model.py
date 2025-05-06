import pytest

from app import create_app
from app import db as _db
from app.models import Role
from app.services.users import create_user


@pytest.fixture(scope='module')
def app():
    """Создание фикстуры для всех тестов в этом модуле."""
    app = create_app('testing')
    with app.app_context():
        yield app       # Доступ к app внутри тестов


@pytest.fixture(scope='module')
def db(app):
    """Фикстура для базы данных (создание и удаление таблиц)."""
    _db.create_all()
    Role.insert_roles()
    yield _db   # Доступ к _db внутри тестов
    _db.session.remove()
    _db.drop_all()


@pytest.fixture(scope='function')
def session(db):
    # Очистка всех таблиц
    for table in reversed(db.metadata.sorted_tables):   # гарантирует правильный порядок удаления (учитывая внешние ключи).
        db.session.execute(table.delete())
    db.session.commit()

    yield db.session

    db.session.rollback()
    db.session.remove()


@pytest.fixture(scope='function')
def test_users(session):
    """Фикстура для создания пользователей."""
    user_1 = create_user(password='cat', email='user_1@example.com', username='testuser1', session=session)
    user_2 = create_user(password='cat', email='user_2@example.com', username='testuser2', session=session)
    session.commit()
    return user_1, user_2


def test_password_setter(test_users):
    user_1, _ = test_users
    assert user_1.password_hash is not None


def test_no_password_getter(test_users):
    user_1, _ = test_users
    with pytest.raises(AttributeError):
        _ = user_1.password


def test_password_verification(test_users):
    user_1, _ = test_users
    assert user_1.verify_password('cat')
    assert not user_1.verify_password('dog')


def test_password_salts_are_random(test_users):
    user_1, user_2 = test_users
    assert user_1.password_hash != user_2.password_hash
