
from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from . import mail


def send_email(app, msg):
    """
    Отправляет email-сообщение с обработкой ошибок.
    Это базовая функция для отправки email.

    Эта функция пытается отправить email-сообщение, используя Flask-Mail. Если при
    отправке возникает ошибка, она логирует исключение и повторно возбуждает его,
    чтобы обеспечить правильную обработку ошибки в вызывающем коде.

    Аргументы:
        - app (Flask): Экземпляр Flask-приложения, необходимый для создания контекста.
        - msg (Message): Объект сообщения Flask-Mail, содержащий данные письма.

    Исключения:
        - Exception: Если произошла ошибка при отправке письма, она логируется и вызывается исключение.

    Примечания:
        - Для отправки сообщения используется контекст приложения Flask.
    """

    try:
        with app.app_context():
            mail.send(msg)
    except Exception as e:
        app.logger.error(f'Error sending email: {e}')
        raise


def create_and_send_email_async(to, subject, template, **kwargs):
    """
    Создает и отправляет email-сообщение в фоновом потоке.

    Эта функция создает объект email-сообщения с использованием заданных данных,
    таких как получатель, тема, отправитель и шаблон для рендеринга тела письма.
    Письмо отправляется асинхронно в фоновом потоке, чтобы не блокировать основной процесс.

    Аргументы:
        - to (str): Адрес получателя письма.
        - subject (str): Тема письма.
        - template (str): Имя шаблона для рендеринга текста и HTML контента письма.
        - \*\*kwargs (dict): Дополнительные параметры для рендеринга шаблона.

    Возвращает:
        - threading.Thread: Поток, в котором выполняется асинхронная отправка письма.

    Примечания:
        - Функция использует настройки приложения для получения префикса темы и отправителя.
        - Отправка письма выполняется в отдельном потоке для повышения производительности.
    """

    app = current_app._get_current_object()
    msg = Message(
        recipients=[to],
        subject=app.config['MAIL_SUBJECT_PREFIX'] + subject,
        sender=app.config['MAIL_SENDER'],
        charset="utf-8"
    )
    # Рендерим текстовую и html версии письма
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    # Запускаем отправку email в фоновом потоке
    thr = Thread(target=send_email, args=[app, msg])
    thr.start()

    return thr
