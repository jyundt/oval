from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, IntegerField,\
                    SelectField, DateTimeField, BooleanField
from wtforms import ValidationError
from wtforms.validators import Required,EqualTo,Optional
from ..models import RaceClass, Racer, Team, Race
from sqlalchemy import and_

class RaceClassForm(Form):
    name = StringField('Name', validators=[Required()])

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

class RaceForm(Form):
    date = DateField('Date', validators=[Required()],
                     description='MM/DD/YYYY',
                     format='%m/%d/%Y')
    class_id = SelectField(u'Race Class', coerce=int, validators=[Required()])
    fast_lap = DateTimeField('Fast Lap', validators=[Optional()],
                             description='mm:ss',default=None,
                             format='%M:%S')
    slow_lap = DateTimeField('Slow Lap', validators=[Optional()],
                             description='mm:ss',default=None,
                             format='%M:%S')
    average_lap = DateTimeField('Average Lap', validators=[Optional()],
                             description='mm:ss',default=None,
                             format='%M:%S')
    weather = StringField('Weather',validators=[Optional()])
    usac_permit = StringField('USAC Permit',validators=[Optional()])
    laps = IntegerField('# of Laps',validators=[Optional()])

    def validate(self):
        if not super(RaceForm, self).validate():
            return False
        if Race.query.filter(and_(Race.date==self.date.data, Race.class_id==self.class_id.data)).all():
            print self.date.data
            print self.class_id.data
            self.date.errors.append('A race for this day and category already exists!')
            self.class_id.errors.append('A race for this day and category already exists!')
            return False
        return True
        


class RaceAddForm(RaceForm):
    submit = SubmitField('Add')

class RaceEditForm(RaceForm):
    submit = SubmitField('Save')

    def __init__(self, race, *args, **kwargs):
        super(RaceEditForm, self).__init__(*args, **kwargs)
        self.race = race
    

class ParticipantForm(Form):
    place = IntegerField('Place',validators=[Optional()])
    name = StringField('Racer Name',validators=[Required()])
    team_name = StringField('Team Name',validators=[Optional()])
    points = IntegerField('Points',validators=[Optional()])
    team_points = IntegerField('Team Points',validators=[Optional()])
    mar_place = IntegerField('MAR Place',validators=[Optional()])
    mar_points = IntegerField('MAR Points',validators=[Optional()])
    point_prime = BooleanField('Point Prime?',validators=[Optional()])
    dnf = BooleanField('DNF?',validators=[Optional()])
    dns = BooleanField('DNS?',validators=[Optional()])
    relegated = BooleanField('Relegated?',validators=[Optional()])
    disqualified = BooleanField('Disqualified?',validators=[Optional()])
    submit = SubmitField('Submit')

    def validate_name(self, field):
        if Racer.query.filter_by(name=field.data).first() is None:
            raise ValidationError('Racer does not exist!')

    def validate_team_name(self, field):
        if Team.query.filter_by(name=field.data).first() is None:
            raise ValidationError('Team does not exist!')
