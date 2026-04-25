from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class RouteForm(FlaskForm):
    name = StringField('НАЗВАНИЕ МАРШРУТА', validators=[DataRequired()])
    description = TextAreaField('ОПИСАНИЕ')
    submit = SubmitField('СОЗДАТЬ МАРШРУТ')