from urllib.parse import urlparse

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..email import send_email
from ..logger import logger
from ..models import User
from . import auth_bp
from .forms import LoginForm, RegistrationForm


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

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
                return redirect(url_for('main_bp.index'))
            return redirect(next_page)

        return redirect(url_for('main_bp.index'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('А нахуя тогда логинился ?')
    return redirect(url_for('main_bp.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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
        send_email(user.email, 'Confirm Your Account', 'auth/email/confirm', user=user, token=token)
        flash('Подтвердите свой адрес email, сэр!')
        return redirect(url_for('main_bp.index'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main_bp.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main_bp.index'))


@auth_bp.before_app_request
def before_request():
    if (current_user.is_authenticated
        and not current_user.confirmed
            and request.endpoint[:5] != 'auth.'):
        return redirect(url_for('auth.unconfirmed'))


@auth_bp.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect('main_bp.index')
    return render_template('auth/unconfirmed.html')


@auth_bp.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm',
               user=current_user,
               token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main_bp.index'))
