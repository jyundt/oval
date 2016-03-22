from flask_wtf import Form
from wtforms import StringField, SubmitField, DateTimeField
from wtforms import ValidationError


class RaceResultsForm(Form):
    test_field = DateTimeField('Date')
    submit = SubmitField('Results!')
