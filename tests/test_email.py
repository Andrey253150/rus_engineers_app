from unittest.mock import ANY, MagicMock, patch

import pytest
from flask import Flask
from flask_mail import Message

from app.email import create_and_send_email_async, send_email


class TestSendEmail:
    """
    Класс для тестирования отправки email.
    """

    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        """
        Общая настройка для всех тестов в классе.
        """

        self.app = Flask(__name__)
        self.mock_mail_send = mocker.patch('app.email.mail.send')
        self.test_message = Message(
            subject='Test',
            sender='noreply@test.com',
            recipients=['test@example.com'],
            body='Test Body')

    def test_send_email_failure(self, caplog):
        """
        Тестируем обработку ошибки при отправке письма.
        """

        # Мокируем mail.send, чтобы он выбрасывал исключение
        self.mock_mail_send.side_effect = Exception('Error sending email: SMTP error')

        # Проверяем, что исключение пробрасывается
        with pytest.raises(Exception) as exc_info:
            send_email(self.app, self.test_message)  # Предполагаем, что `app` доступен в контексте

            # Проверяем, что ошибка была залогирована
            assert 'SMTP error' in str(exc_info.value)
            assert 'Error sending email: SMTP error' in caplog.text

    def test_send_email_success(self):
        """
        Тестируем успешную отправку письма.
        """
        # Мокируем mail.send, чтобы он ничего не делал (успешная отправка)
        self.mock_mail_send.return_value = None
        send_email(self.app, self.test_message)
        self.mock_mail_send.assert_called_once_with(self.test_message)

    def test_create_and_send_email_async(self):
        """Тестируем асинхронное создание и отправку письма.

        Назначение:
        Функция предназначена для тестирования асинхронного создания и отправки электронного письма
        с использованием моков (mock-объектов) для изоляции тестируемого кода от внешних зависимостей.

        Структура теста:
        1. Мокирование зависимостей:
            - Используется `patch` для мокирования (т.е. имитации):
                - `app.email.render_template` — для рендеринга шаблонов.
                - `app.email.Message` — для создания объекта сообщения.
                - `app.email.Thread` — для создания и управления потоком (thread).
            Здесь важно, что `patch` работает на уровне модулей, поэтому нужно указать,
            где именно находится зависимость, которую надо заменить.

        2. Настройка моков:
            - `mock_render_template` настраивается для возврата строки с именем шаблона.
            - `mock_message` настраивается для возврата мокированного экземпляра сообщения
                (`mock_message_instance`).

        3. Вызывается функция `create_and_send_email_async` с параметрами.
           Здесь важно, что когда `create_and_send_email_async` вызывает Thread,
           она на самом деле вызывает мок-объект.

        4. Проверка создания потока:
            - Проверяется, что поток создан с правильными аргументами:
                - `target=send_email` — целевая функция для выполнения в потоке.
                - `args=[ANY, mock_message_instance]` — аргументы для целевой функции.

        5. Проверка запуска потока:
            - Проверяется, что поток был запущен с помощью вызова `start`.

        6. Проверка рендеринга шаблонов:
            - Проверяется, что шаблоны были отрендерены с правильными параметрами:
                - `test_template.txt` и `test_template.html` с параметром `some_key='some_value'`.

        7. Проверка возвращаемого значения:
            - Проверяется, что функция возвращает объект потока (`mock_thread.return_value`).

        Ключевые моменты:
            - Изоляция теста: Использование моков позволяет изолировать тест от реальных зависимостей,
            таких как рендеринг шаблонов и отправка писем.
            - Проверка асинхронности: Тест проверяет, что функция корректно создает и запускает поток
            для асинхронной отправки письма.
            - Проверка возвращаемого значения: Убеждаемся, что функция возвращает ожидаемый объект потока.
        """
        # Получение моков
        with (patch('app.email.render_template') as mock_render_template,
              patch('app.email.Message') as mock_message,
              patch('app.email.Thread') as mock_thread):

            # Настройка моков
            mock_render_template.side_effect = lambda x, **kwargs: f"Rendered {x}"
            mock_message_instance = MagicMock()
            mock_message.return_value = mock_message_instance

            # Вызываем тестируемую функцию
            thr = create_and_send_email_async(
                to='test@example.com',
                subject='Test Subject',
                template='test_template',
                some_key='some_value')

            # Поток создан с правильными аргументами
            mock_thread.assert_called_once_with(
                target=send_email,
                args=[ANY, mock_message_instance])

            # Поток был запущен
            mock_thread.return_value.start.assert_called_once()

            # Шаблоны рендерятся
            mock_render_template.assert_any_call('test_template.txt', some_key='some_value')
            mock_render_template.assert_any_call('test_template.html', some_key='some_value')

            # Возвращается объект потока
            assert thr == mock_thread.return_value
