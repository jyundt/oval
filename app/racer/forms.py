from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, IntegerField, \
    BooleanField, SelectField
from wtforms import ValidationError
from wtforms.validators import Required, Optional

from ..models import Racer, Team


class RacerForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    usac_license = IntegerField('USAC License', validators=[Optional()])
    birthdate = DateField('Birthdate', validators=[Optional()],
                          description="MM/DD/YYYY",
                          format='%m/%d/%Y')
    current_team = StringField('Current Team', validators=[Optional()])
    aca_membership = SelectField('Current ACA Membership')
    paid = BooleanField('Paid', validators=[Optional()])

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


class RacerAddForm(RacerForm):
    submit = SubmitField('Add')

    def validate_usac_license(self, field):
        if Racer.query.filter_by(usac_license=field.data).first():
            raise ValidationError('USAC license already in use.')


class RacerSearchForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Search')
