from datetime import datetime, timezone
from pathlib import Path
from threading import Thread

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)
from flask_bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from config import config

app = Flask(__name__)
app.config.from_object(config['default'])

basedir = Path(__file__).resolve().parent


toolbar = DebugToolbarExtension(app)
Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)

# Создание миграций
migrate = Migrate(app, db)
mail = Mail(app)


# Определение модели Role
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

    # Атрибут users это объектно-ориентированное представление отношения.
    # При обращении к атрибуту users будет возвращаться список
    # пользователей с данной ролью.

    # Аргумент backref определяет обратную ссылку отношения –
    # атрибут role в модели User.
    # Данный атрибут можно использовать вместо role_id для доступа
    # к модели Role как к объекту.
    # Присовение атрибуту lazy='dynamic' означает возврат не самих
    # элементов - пользователей, а запрос для возврата этих элементов.
    # Это делается для применения дополнительных фильтров/сортировок
    # вида role_user.users.order_by(User.username).all().
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)

    # Внешний ключ для отношения с таблицей roles
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=2)

    def __repr__(self):
        return f'<User {self.username}>'


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


# Функция для отправки email в отдельном потоке
def send_async_email(app, msg):
    # Создаем контекст приложения, так как Flask-Mail требует его
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    msg = Message(
            subject=app.config['MAIL_SUBJECT_PREFIX'] + subject,
            sender=app.config['MAIL_SENDER'],
            recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


@app.route('/', methods=['GET', 'POST'])
def index():
    user_agent = request.headers.get('User-Agent')
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            session['known'] = False
            flash(f'Тебя добавили в нашу базу, {user.username}!')
            if app.config['MAIL_USERNAME']:
                send_email(
                    to=app.config['MAIL_USERNAME'],
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
        return redirect(url_for('index'))
    return render_template(
        'index.html',
        user_agent=user_agent,
        current_time=datetime.now(timezone.utc),
        form=form,
        name=session.get('name'),
        known=session.get('known'))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
