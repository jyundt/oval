from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, IntegerField,\
                    SelectField, DateTimeField
from wtforms import ValidationError
from wtforms.validators import Required,EqualTo,Optional
from ..models import RaceClass, Racer, Team, Race

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
                          description="MM/DD/YYYY",
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

class RaceForm(Form):
    date = DateField('Date', validators=[Required()],
                     description='MM/DD/YYYY',
                     format='%m/%d/%Y')
    class_id = SelectField(u'Race Class', coerce=int, validators=[Required()])
    fast_lap = DateTimeField('Fast Lap', validators=[Optional()],
                             description='mm:ss',
                             format='%M:%S')
    slow_lap = DateTimeField('Slow Lap', validators=[Optional()],
                             description='mm:ss',
                             format='%M:%S')
    average_lap = DateTimeField('Average Lap', validators=[Optional()],
                             description='mm:ss',
                             format='%M:%S')
    weather = StringField('Weather',validators=[Optional()])
    usac_permit = StringField('USAC Permit',validators=[Optional()])
    laps = IntegerField('# of Laps',validators=[Optional()])
    submit = SubmitField('Submit')
