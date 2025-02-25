from urllib.parse import urlparse

from flask import (current_app, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..email import create_and_send_email_async
from ..logger import logger
from ..models import User
from . import auth_bp
from .forms import LoginForm, RegistrationForm


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Залогинивание пользователя."""

    # Если пользователь уже аутентифицирован, перенаправляем его на главную страницу
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Проверка пользователя и пароля
        if user is None or not user.verify_password(form.password.data):
            logger.warning(f'Неудачная попытка входа для email: {form.email.data}')
            flash('Неверный емэйл или пароль, дядь. Ебани еще разок!', 'error')
            return redirect(url_for('.login'))

        # Вход пользователя
        login_user(user, remember=form.remember_me.data)
        logger.info(f'Пользователь {user.email} успешно вошёл в систему.')

        # Проверка безопасности URL, запрошенного до входа, на то,
        # что от является относительным без домена. Это предотвращает
        # атаки с открытым перенаправлением.
        next_page = request.args.get('next')
        if next_page:
            next_url = urlparse(next_page)
            if next_url.netloc != '':  # Проверка содержания домена в URL
                return redirect(url_for('main.index'))
            return redirect(next_page)

        return redirect(url_for('main.index'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя."""
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            username=form.username.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        create_and_send_email_async(
            user.email,
            'Подтверждение аккаунта.',
            'auth/email/confirm',
            user=user,
            token=token)
        flash('Письмо с подтверждением отправлено на почту, сэр!')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    """Подтверждение почтового ящика пользователя.
    Значение параметра token берется из эндпоинта.
    А эндпоинт был выслан в почту до этого на этапе регистрации.
    """
    if current_user.confirmed:
        flash('Ты уже подтвердил свой email до этого, боец. Вольно!')
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('Почтовый ящик подтвержден, теперь ты в круге доверия!')
    else:
        flash('Со ссылкой что-то не то: или старая, или битая. Я хз.')
    return redirect(url_for('main.index'))


@auth_bp.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main.index')
    return render_template('auth/unconfirmed.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('А нахуя тогда логинился ?')
    return redirect(url_for('main.index'))


@auth_bp.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    create_and_send_email_async(current_user.email, 'Confirm Your Account', 'auth/email/confirm',
                                user=current_user,
                                token=token)
    flash('Новое письмо для подтверждения аккаунта отправлено на почтовый ящик.')
    return redirect(url_for('main.index'))


@auth_bp.before_app_request
def before_request():
    """Функция для ограничения доступа неподтвержденных пользователей.
    Работает для всего приложения (не только для макета auth).
    Неподтвержденному пользователю разрешается доступ только в зону auth/ .
    """
    if (current_user.is_authenticated
            and not current_user.confirmed
            and request.endpoint != 'static'    # Загрузка стаитики без проверки
            and request.endpoint[:5] != 'auth.'):
        current_app.logger.debug(
            f"Пользователь {current_user.id} не подтвержден. Перенаправляю на специальную страницу."
        )
        return redirect(url_for('auth.unconfirmed'))
