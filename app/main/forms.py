from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, IntegerField
from wtforms import ValidationError
from wtforms.validators import Required,EqualTo,Optional
from ..models import RaceClass, Racer, Team

class RaceClassForm(Form):
    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_name(self, field):
        if RaceClass.query.filter(RaceClass.name.ilike(
                                                       field.data)).first():
            raise ValidationError('Race class name already in use.')

class RacerForm(Form):
    name = StringField('Name', validators=[Required()])
    usac_license = IntegerField('USAC License', validators=[Optional()])
    birthdate = DateField('Birthdate', validators=[Optional()],
                          description="Example: 01/27/1986",
                          format='%m/%d/%Y' )
    submit = SubmitField('Submit')

    def validate_usac_license(self, field):
        if Racer.query.filter_by(usac_license=field.data).first():
            raise ValidationError('USAC license already in use.')

class TeamForm(Form):
    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_name(self, field):
        if Team.query.filter(Team.name.ilike(field.data)).first():
            raise ValidationError('Team name already in use.')
