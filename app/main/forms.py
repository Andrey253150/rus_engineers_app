from flask_wtf import FlaskForm
from sqlalchemy import select
from wtforms import (BooleanField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import DataRequired, Email, Length, Regexp

from .. import db
from ..models import Role, User


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Сохранить')


class EditProfileForm(FlaskForm):
    name = StringField('Имя', validators=[Length(0, 64)])
    location = StringField('Адрес', validators=[Length(0, 64)])
    about_me = TextAreaField('Обо мне')
    submit = SubmitField('Сохранить')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Почта', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Логин', validators=[
        DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                                              'Usernames must have only letters, '
                                              'numbers, dots or underscores')])
    confirmed = BooleanField('Email подтвержден')
    role = SelectField('Роль', coerce=int)
    name = StringField('Имя (полностью)', validators=[Length(0, 64)])
    location = StringField('Адрес', validators=[Length(0, 64)])
    about_me = TextAreaField('Обо мне')
    submit = SubmitField('Сохранить')

    def __init__(self, user, *args, **kwargs):
        super(self).__init__(*args, **kwargs)
        self.user = user
        self.role.choices = [(role.id, role.name) for role in
                             db.session.scalars(select(Role).order_by(Role.name))]

    def validate_email(self, field):
        if (field.data != self.user.email and
                db.session.scalar(select(User).where(User.email == field.data))):
            raise ValidationError('Email уже зарегистрирован.')

    def validate_username(self, field):
        if (field.data != self.user.username and
                db.session.scalar(select(User).where(User.username == field.data))):
            raise ValidationError('Это имя пользователя уже занято.')


class PostForm(FlaskForm):
    body = TextAreaField("Введите текст поста...")
    submit = SubmitField('Сохранить')


class CommentForm(FlaskForm):
    body = StringField('Напишите комментарий...', validators=[DataRequired()])
    submit = SubmitField('Сохранить')
