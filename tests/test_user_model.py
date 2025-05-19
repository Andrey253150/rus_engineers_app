"""Тесты пользователей и паролей.

Этот модуль использует фикстуры `pytest` для поэтапной подготовки окружения
и создания тестовых пользователей. Ниже описана цепочка зависимостей фикстур.

Цепочка вызовов фикстур:

.. code-block:: text

    test_password_setter
    └── test_users
        └── session
            └── db
                └── app

Описание фикстур:

- ``app``:
    Создаёт Flask-приложение с тестовой конфигурацией и активирует его контекст.

- ``db(app)``:
    Создаёт все таблицы в базе данных перед началом тестов.
    После выполнения тестов — удаляет таблицы и очищает сессию.

- ``session(db)``:
    Перед каждым тестом удаляет все записи из всех таблиц (без удаления самих таблиц).
    После теста — откатывает транзакцию и очищает сессию.

- ``test_users(session)``:
    Создаёт двух тестовых пользователей и сохраняет их в базе данных.
    Используется в тестах как исходный набор данных.

Преимущества такой структуры:

- Тесты полностью изолированы друг от друга.
- База данных всегда находится в чистом состоянии.
- Простая иерархия зависимостей обеспечивает читаемость и предсказуемость выполнения.

"""
import pytest

from app import create_app
from app import db as _db
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
