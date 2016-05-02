from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, IntegerField
from wtforms import ValidationError
from wtforms.validators import Required, Optional
from ..models import Racer, Team

class RacerForm(Form):
    name = StringField('Name', validators=[Required()])
    usac_license = IntegerField('USAC License', validators=[Optional()])
    birthdate = DateField('Birthdate', validators=[Optional()],
                          description="MM/DD/YYYY",
                          format='%m/%d/%Y')
    current_team = StringField('Current Team', validators=[Optional()])
    strava_id = IntegerField('Strava athlete ID', validators=[Optional()])


    def validate_current_team(self, field):
        if Team.query.filter_by(name=field.data).first() is None:
            raise ValidationError('Team does not exist!')

class RacerEditForm(RacerForm):
    submit = SubmitField('Save')

    def __init__(self, racer, *args, **kwargs):
        super(RacerEditForm, self).__init__(*args, **kwargs)
        self.racer = racer

    def validate_usac_license(self, field):
        if field.data != self.racer.usac_license and \
            Racer.query.filter_by(usac_license=field.data).first():
            raise ValidationError('USAC license already in use!')

    def validate_strava_id(self, field):
        if field.data != self.racer.strava_id and \
            Racer.query.filter_by(strava_id=field.data).first():
            raise ValidationError('Strava athlete ID already in use!')

class RacerAddForm(RacerForm):
    submit = SubmitField('Add')

    def validate_usac_license(self, field):
        if Racer.query.filter_by(usac_license=field.data).first():
            raise ValidationError('USAC license already in use.')

    def validate_strava_id(self, field):
        if Racer.query.filter_by(strava_id=field.data).first():
            raise ValidationError('Strava athlete ID already in use.')

class RacerSearchForm(Form):
    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Search')

