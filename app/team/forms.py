from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Required
from ..models import Racer, Team

class RacerAddToTeamForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Racer.query.filter_by(name=field.data).first() is None:
            raise ValidationError('Racer does not exist!')

class TeamForm(FlaskForm):
    name = StringField('Name', validators=[Required()])

class TeamEditForm(TeamForm):
    submit = SubmitField('Save')

    def __init__(self, team, *args, **kwargs):
        super(TeamEditForm, self).__init__(*args, **kwargs)
        self.team = team

    def validate_name(self, field):
        if field.data != self.team.name and \
            Team.query.filter(Team.name.ilike(field.data)).first():
            raise ValidationError('Team name already in use.')

class TeamAddForm(TeamForm):
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Team.query.filter(Team.name.ilike(field.data)).first():
            raise ValidationError('Team name already in use.')
