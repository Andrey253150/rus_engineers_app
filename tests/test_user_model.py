import unittest

from app.models import User


class UserModelTestCase(unittest.TestCase):
    """Проверка функций хеширования паролей."""

    def setUp(self):
        """Создаем фикстуры."""
        self.u = User(password='cat')
        self.u2 = User(password='cat')

    def test_password_setter(self):
        """Тестируем установку пароля."""
        self.assertIsNotNone(self.u.password_hash)

    def test_no_password_getter(self):
        """Тестируем отсутствие доступа к паролю напрямую."""
        # Ожидаем, что внутри блока будет выброшено исключение типа AttributeError.
        # Если исключение происходит, оно перехватывается и передается в assertRaises.
        # Если исключение выбрасывается, то оно фиксируется, и тест проходит успешно.
        with self.assertRaises(AttributeError):
            self.u.password

    def test_password_verification(self):
        """Тестируем правильность проверки пароля."""
        self.assertTrue(self.u.verify_password('cat'))
        self.assertFalse(self.u.verify_password('dog'))

    def test_password_salts_are_random(self):
        """Тестируем, что соли паролей генерируются случайным образом."""
        self.assertTrue(self.u.password_hash != self.u2.password_hash)


if __name__ == '__main__':
    unittest.main()
