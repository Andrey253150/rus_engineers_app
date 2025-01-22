from datetime import datetime, timezone
from pathlib import Path

from flask import (current_app, flash, redirect, render_template, request,
                   session, url_for)

from .. import db
from ..email import send_email
from ..models import User
from . import main_bp
from .forms import NameForm

basedir = Path(__file__).resolve().parent


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    user_agent = request.headers.get('User-Agent')
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            session['known'] = False
            flash(f'Тебя добавили в нашу базу, {user.username}!')
            if current_app.config['MAIL_USERNAME']:
                send_email(
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
    return render_template('user.html', name=name)
