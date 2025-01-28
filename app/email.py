
import logging
from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from . import mail


# Функция для отправки email в фоновом потоке
def send_async_email(app, msg):
    try:
        # Используем контекст приложения: требование Flask-Mail
        with app.app_context():
            print(msg.as_string())
            mail.send(msg)
    except Exception as e:
        app.logger.error(f'Error sending email: {e}')
        raise


# Основная функция отправки email
def send_email(to, subject, template, **kwargs):
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
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()

    return thr
