from flask_wtf import Form
from wtforms import StringField, SubmitField, DateTimeField
from wtforms import ValidationError
from wtforms.validators import Required,EqualTo


class RaceClassForm(Form):
    race_class_description = StringField('Race Type/Description', validators=[Required()])
    submit = SubmitField('Add')
