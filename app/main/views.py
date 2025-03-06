"""Маршруты для главного Blueprint.

Этот модуль отвечает за обработку маршрутов главного Blueprint, включая:
    - Главную страницу, где пользователи могут вводить своё имя.
    - Страницу пользователя, отображающую переданное имя.

Функции:
    - `index()`: Главная страница, обработка формы пользователя.
    - `user(name)`: Страница пользователя.

Дополнительно:
    - Взаимодействие с базой данных.
    - Отправка уведомлений по электронной почте (если настроено).
"""
from datetime import datetime, timezone
from pathlib import Path

from flask import (current_app, flash, redirect, render_template, request,
                   session, url_for)

from .. import db
from ..email import create_and_send_email_async
from ..logger import LOG_FILE
from ..models import User
from . import main_bp
from .forms import NameForm

basedir = Path(__file__).resolve().parent


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Главная страница. Обрабатывает ввод имени пользователя.

    - Проверяет, существует ли пользователь в базе данных.
    - Если нет, добавляет его и отправляет уведомление (если настроена почта).
    - Сохраняет имя и статус (известен/неизвестен) в сессии.

    Возвращает:
        Response: Шаблон главной страницы с параметрами пользователя.
    """
    current_app.logger.info('Обращение к главной странице')
    user_agent = request.headers.get('User-Agent')
    form = NameForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.username == form.name.data))
        if user is None:
            user = User(username=form.name.data)
            session['known'] = False
            flash(f'Тебя добавили в нашу базу, {user.username}!')
            if current_app.config['MAIL_USERNAME']:
                create_and_send_email_async(
                    to=current_app.config['MAIL_USERNAME'],
                    subject='New User',
                    template='mail/new_user',
                    user=user
                )
            db.session.add(user)
            db.session.commit()
        else:
            session['known'] = True
            flash(f'Ты уже есть в нашей базе, {user.username}!')
        session['name'] = form.name.data
        return redirect(url_for('.index'))
    return render_template(
        'index.html',
        user_agent=user_agent,
        current_time=datetime.now(timezone.utc),
        form=form,
        name=session.get('name'),
        known=session.get('known'))


@main_bp.route('/user/<name>')
def user(name):
    """Страница пользователя.

    Аргументы:
        name (str): Имя пользователя, отображаемое на странице.

    Возвращает:
        Response: Шаблон страницы пользователя.
    """
    return render_template('user.html', name=name)


@main_bp.route('/error500')
def trigger_500():
    # Искусственно вызываем ошибку 500
    raise Exception("Это тестовая ошибка 500")


@main_bp.route("/logs")
def show_logs():
    """Читает логи из файла и передаёт их в HTML-шаблон."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
    except FileNotFoundError:
        logs = ["Лог-файл пока не создан."]

    return render_template("logs.html", logs=logs)
