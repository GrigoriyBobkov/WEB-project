from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    username = StringField('ИМЯ ПОЛЬЗОВАТЕЛЯ', validators=[DataRequired()])
    password = PasswordField('ПАРОЛЬ', validators=[DataRequired()])
    password_again = PasswordField('ПОВТОРИТЕ ПАРОЛЬ', validators=[DataRequired()])
    submit = SubmitField('ЗАРЕГИСТРИРОВАТЬСЯ')


class LoginForm(FlaskForm):
    username = StringField('ИМЯ ПОЛЬЗОВАТЕЛЯ', validators=[DataRequired()])
    password = PasswordField('ПАРОЛЬ', validators=[DataRequired()])
    submit = SubmitField('ВОЙТИ')