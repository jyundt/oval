from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Required
from ..models import Official

class OfficialForm(FlaskForm):
    name = StringField('Name', validators=[Required()])

class OfficialEditForm(OfficialForm):
    submit = SubmitField('Save')

    def __init__(self, official, *args, **kwargs):
        super(OfficialEditForm, self).__init__(*args, **kwargs)
        self.official = official

    def validate_name(self, field):
        if field.data != self.official.name and \
           Official.query.filter(Official.name.ilike(field.data)).first():
            raise ValidationError('Official already exists!.')

class OfficialAddForm(OfficialForm):
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Official.query.filter(Official.name.ilike(field.data)).first():
            raise ValidationError('Official already exists!.')
