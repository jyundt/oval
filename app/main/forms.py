from flask_wtf import Form
from wtforms import StringField, SubmitField, DateTimeField, IntegerField
from wtforms import ValidationError
from wtforms.validators import Required,EqualTo
from ..models import RaceClass

class RaceClassEditForm(Form):
    race_class_name = StringField('Name', validators=[Required()])
    submit = SubmitField('Save')

    def validate_race_class_name(self, field):
        if RaceClass.query.filter(RaceClass.name.ilike(
                                                       field.data)).first():
            raise ValidationError('Race class name already in use.')

class RaceClassAddForm(Form):
    race_class_id = IntegerField('Database ID', validators=[Required()])
    race_class_name = StringField('Name', validators=[Required()])
    submit = SubmitField('Add')

    def validate_race_class_id(self, field):
        if RaceClass.query.get(field.data):
            raise ValidationError('Race class ID already in use.')

    def validate_race_class_name(self, field):
        if RaceClass.query.filter(RaceClass.name.ilike(
                                                       field.data)).first():
            raise ValidationError('Race class name already in use.')
