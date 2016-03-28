from flask_wtf import Form
from wtforms import StringField, SubmitField, DateTimeField, IntegerField
from wtforms import ValidationError
from wtforms.validators import Required,EqualTo


class RaceClassAddForm(Form):
    race_class_description = StringField('Race Type/Description',
                                         validators=[Required()])
    submit = SubmitField('Add')

class RaceClassEditForm(Form):
    race_class_id = IntegerField('Database ID', validators=[Required()])
    race_class_description = StringField('Name', validators=[Required()])
    submit = SubmitField('Save')
