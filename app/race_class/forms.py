from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Required, Optional, Regexp
from ..models import RaceClass

class RaceClassForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    color = StringField('Race Category Color',
                        validators=[Optional(),
                                    Regexp('^#(?:[0-9a-fA-F]{3}){1,2}$',
                                           0,
                                           'Color must be valid hex format.\
                                            (example: #ff0000)')],
                        description='#ff0000')

class RaceClassEditForm(RaceClassForm):
    submit = SubmitField('Save')

    def __init__(self, race_class, *args, **kwargs):
        super(RaceClassEditForm, self).__init__(*args, **kwargs)
        self.race_class = race_class

    def validate_name(self, field):
        if field.data != self.race_class.name and \
           RaceClass.query.filter(RaceClass.name.ilike(field.data)).first():
            raise ValidationError('Race class name already in use.')

class RaceClassAddForm(RaceClassForm):
    submit = SubmitField('Add')

    def validate_name(self, field):
        if RaceClass.query.filter(RaceClass.name.ilike(field.data)).first():
            raise ValidationError('Race class name already in use.')

