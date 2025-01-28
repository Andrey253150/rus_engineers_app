from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, StringField, SubmitField,
                     ValidationError)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

from ..models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(1, 64),
            Regexp(
                '^[A-Za-z][A-Za-z0-9_.]*$',
                0,
                'Допускаются только буквы, цифры, точки и нижние подчеркивания.'
            )
        ]
    )

    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         EqualTo('password2', message='Пароли должны совпадать.')])
    password2 = PasswordField('Подтвердите введеный пароль', validators=[DataRequired()])
    submit = SubmitField('Register')

    # Кастомные валидаторы. Вызываются автоматически вместе с другими валидаторами.
    # Валидация email. Параметр field встроенный и подставляется из имени метода.
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Данный email уже зарегистрирован.')

    # Валидация username. Параметр field встроенный и подставляется из имени метода.
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Имя пользователя уже занято.')

    # # Отключена чтобы не заморачиваться.
    # # Валидация password.
    # def validate_password(self, field):
    #     password = field.data

    #     if len(password) < 8:
    #         raise ValidationError('Пароль должен содержать не менее 8 символов.')
    #     if not any(char.isdigit() for char in password):
    #         raise ValidationError('Пароль должен содержать хотя бы одну цифру.')
    #     if not any(char.isupper() for char in password):
    #         raise ValidationError('Пароль должен содержать хотя бы одну заглавную букву.')
    #     if not any(char.islower() for char in password):
    #         raise ValidationError('Пароль должен содержать хотя бы одну строчную букву.')
