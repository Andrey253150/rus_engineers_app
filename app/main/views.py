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

from flask import (abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import current_user, login_required
from sqlalchemy import select

from .. import db
from ..decorators import admin_required, permission_required
from ..email import create_and_send_email_async
from ..logger import LOG_FILE
from ..models import Permission, Post, Role, User
from . import main_bp
from .forms import EditProfileAdminForm, EditProfileForm, NameForm, PostForm

basedir = Path(__file__).resolve().parent


# @main_bp.route('/', methods=['GET', 'POST'])
# def index():
#     """Главная страница. Обрабатывает ввод имени пользователя.

#     - Проверяет, существует ли пользователь в базе данных.
#     - Если нет, добавляет его и отправляет уведомление (если настроена почта).
#     - Сохраняет имя и статус (известен/неизвестен) в сессии.

#     Возвращает:
#         Response: Шаблон главной страницы с параметрами пользователя.
#     """
#     current_app.logger.info('Обращение к главной странице')
#     user_agent = request.headers.get('User-Agent')
#     form = NameForm()
#     if form.validate_on_submit():
#         user = db.session.scalar(select(User).where(User.username == form.name.data))
#         if user is None:
#             user = User(username=form.name.data)
#             session['known'] = False
#             flash(f'Тебя добавили в нашу базу, {user.username}!')
#             if current_app.config['MAIL_USERNAME']:
#                 create_and_send_email_async(
#                     to=current_app.config['MAIL_USERNAME'],
#                     subject='New User',
#                     template='mail/new_user',
#                     user=user
#                 )
#             db.session.add(user)
#             db.session.commit()
#         else:
#             session['known'] = True
#             flash(f'Ты уже есть в нашей базе, {user.username}!')
#         session['name'] = form.name.data
#         return redirect(url_for('.index'))
#     return render_template(
#         'index.html',
#         user_agent=user_agent,
#         current_time=datetime.now(timezone.utc),
#         form=form,
#         name=session.get('name'),
#         known=session.get('known'))

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    current_app.logger.info('Обращение к главной странице')
    user_agent = request.headers.get('User-Agent')
    form = PostForm()
    user = current_user._get_current_object()
    if (current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit()):
        post = Post(body=form.body.data, author=current_user._get_current_object())
        if len(post.body) == 0:
            flash("Нельзя публиковать пустые сообщения!")
            return redirect(url_for('.index'))
        db.session.add(post)
        db.session.commit()
        flash('Пост успешно опубликован!')
        current_app.logger.info(f'Поьлзователь {user} опубликовал пост.')
        return redirect(url_for('.index'))

    # Получение номера страницы из параметра запроса
    page = request.args.get('page', 1, type=int)

    # Пагинация постов
    posts_pagination = db.paginate(
        select(Post).order_by(Post.timestamp.desc()),
        page=page,
        per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False)  # Возвращает пустой список вместо 404 при неверной странице

    return render_template(
        'index.html',
        form=form,
        posts=posts_pagination.items,         # Список постов
        pagination=posts_pagination,          # Объект пагинации
        current_time=datetime.now(timezone.utc),
        user_agent=user_agent,
        user=user)


@main_bp.route('/profile/<username>')
def profile(username):
    """Страница пользователя.

    Аргументы:
        username (str): Имя пользователя, отображаемое на странице.

    Возвращает:
        Response: Шаблон страницы пользователя.
    """

    try:
        stmt = select(User).where(User.username == username)
        user = db.session.scalar(stmt)
    except Exception as e:
        current_app.logger.error(f'Ошибка при получении пользователя: {e}')
        abort(500)

    if user is None:
        current_app.logger.info(f"Пользователь не найден: {username}")
        abort(404)

    page = request.args.get('page', 1, type=int)
    posts_pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )

    return render_template(
        'profile.html',
        user=user,
        posts=posts_pagination.items,
        pagination=posts_pagination)


@main_bp.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Ваш профиль успешно обновлен.')
        return redirect(url_for('main.profile', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main_bp.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = db.session.get(User, id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('Профиль пользователя успешно обновлен.')
        return redirect(url_for('main.profile', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main_bp.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    # user = User.query.filter_by(username=username).first()
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        flash('Нет этого пользователя.')
        return redirect(url_for('.index'))

    if current_user.is_following(user):
        flash('Вы уже подписаны на этого пользователя.')
        return redirect(url_for('.profile', username=username))

    current_user.follow(user)
    flash('Вы подписались на %s.' % username)
    return redirect(url_for('.profile', username=username))


@main_bp.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    # user = User.query.filter_by(username=username).first()
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        flash('Нет этого пользователя.')
        return redirect(url_for('.index'))

    if not current_user.is_following(user):
        flash('Вы не подписаны на этого пользователя.')
        return redirect(url_for('.profile', username=username))

    current_user.unfollow(user)
    flash('Вы отписались от %s.' % username)
    return redirect(url_for('.profile', username=username))


@main_bp.route('/followers/<username>')
def followers(username):
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        flash('Нет этого пользователя.')
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page=page,
        per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)

    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template(
        'followers_or_subscriptions.html',
        user=user,
        title="Followers of",
        endpoint='.followers',
        pagination=pagination,
        follows=follows)


@main_bp.route('/subscriptions/<username>')
def followed_by(username):
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        flash('Нет этого пользователя.')
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page=page,
        per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)

    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template(
        'followers_or_subscriptions.html',
        user=user,
        title="Subscriptions of",
        endpoint='.subscriptions',
        pagination=pagination,
        follows=follows)


@main_bp.route('/post/<int:id>')
def post_details(id):
    post = db.session.scalars(select(Post).where(Post.id == id)).all()
    return render_template('post_details.html', posts=post)


@main_bp.route('/edit-post/<int:id>', methods=['GET', 'POST'])
@login_required
def post_edit(id):
    post = db.session.scalar(select(Post).where(Post.id == id))
    if post.author != current_user and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        try:
            db.session.add(post)
            db.session.commit()
            flash('Текст поста успешно обновлен.')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Ошибка при получении пользователя: {e}')
            abort(500)
        return redirect(url_for('.post_details', id=post.id))
    form.body.data = post.body
    return render_template('post_edit.html', form=form)


@main_bp.route('/delete-post/<int:id>', methods=['GET', 'DELETE'])
@login_required
def post_delete(id):
    # Получаем номер текущей страницы из параметров запроса
    page = request.args.get('page', 1, type=int)

    post = db.session.scalar(select(Post).where(Post.id == id))
    if post.author != current_user and not current_user.can(Permission.ADMINISTER):
        abort(403)
    db.session.delete(post)
    db.session.commit()

    return redirect(url_for('.index', page=page))


@main_bp.route("/logs")
def show_logs():
    """Читает логи из файла и передаёт их в HTML-шаблон."""
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
    except FileNotFoundError:
        logs = ["Лог-файл пока не создан."]

    return render_template("logs.html", logs=logs)


@main_bp.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For administrators!"


@main_bp.route('/error500')
def trigger_500():
    """Функция для искусственного вызыва ошибки 500."""
    raise Exception("Это тестовая ошибка 500")
