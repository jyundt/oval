from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, DateField, IntegerField,\
                    SelectField, DateTimeField, BooleanField, TextAreaField
from wtforms import ValidationError
from wtforms.validators import Required, Optional, NumberRange
from ..models import Race, Racer, Team
from sqlalchemy import and_

class RaceForm(FlaskForm):
    date = DateField('Date', validators=[Required()],
                     description='MM/DD/YYYY',
                     format='%m/%d/%Y')
    class_id = SelectField(u'Race Class', coerce=int, validators=[Required()])
    course_id = SelectField(u'Course Type', coerce=int, validators=[Required()])
    weather = StringField('Weather', validators=[Optional()])
    usac_permit = StringField('USAC Permit', validators=[Optional()])
    laps = IntegerField('# of Laps', validators=[Optional()])
    winning_time = DateTimeField('Winning Time', validators=[Optional()],
                                description='hh:mm:ss', default=None,
                                format='%H:%M:%S')
    fast_lap = DateTimeField('Fast Lap', validators=[Optional()],
                             description='mm:ss', default=None,
                             format='%M:%S')
    slow_lap = DateTimeField('Slow Lap', validators=[Optional()],
                             description='mm:ss', default=None,
                             format='%M:%S')
    average_lap = DateTimeField('Average Lap', validators=[Optional()],
                                description='mm:ss', default=None,
                                format='%M:%S')
    starters = IntegerField('# of Starters', validators=[Optional()])
    notes = TextAreaField('Race notes', validators=[Optional()])
    points_race = BooleanField('Points Race', validators=[Optional()])
    picnic_race = BooleanField('Picnic Race', validators=[Optional()])

class RaceAddForm(RaceForm):
    submit = SubmitField('Add')
    submit_another = SubmitField('Add + add another')

    def validate(self):
        if not super(RaceForm, self).validate():
            return False
        if Race.query.filter(and_(Race.date == self.date.data,\
                             Race.class_id == self.class_id.data)).all():
            self.date.errors.append('A race for this day and \
                                     category already exists!')
            self.class_id.errors.append('A race for this day and \
                                         category already exists!')
            return False
        return True

class RaceEditForm(RaceForm):
    submit = SubmitField('Save')

    def __init__(self, race, *args, **kwargs):
        super(RaceEditForm, self).__init__(*args, **kwargs)
        self.race = race


    def validate(self):
        if not super(RaceForm, self).validate():
            return False
        if self.date.data == self.race.date and \
           self.class_id.data == self.race.class_id:
            return True
        elif Race.query.filter(and_(Race.date == self.date.data,\
                             Race.class_id == self.class_id.data)).all():
            self.date.errors.append('A race for this day and \
                                     category already exists!')
            self.class_id.errors.append('A race for this day and \
                                         category already exists!')
            return False
        return True

class RaceSearchForm(FlaskForm):
    date = DateField('Date', validators=[Required()],
                     description='MM/DD/YYYY',
                     format='%m/%d/%Y')
    submit = SubmitField('Search')

class ParticipantForm(FlaskForm):
    place = IntegerField('Place', validators=[Optional(), NumberRange(min=1)])
    name = StringField('Racer Name', validators=[Required()])
    team_name = StringField('Team Name', validators=[Optional()])
    points = IntegerField('Points',
                          validators=[Optional(),
                                      NumberRange(min=1,
                                                  max=11,
                                                  message='Invalid amount of\
                                                  points')])
    team_points = IntegerField('Team Points',
                               validators=[Optional(),
                                           NumberRange(min=1,
                                                       max=10,
                                                       message='Invalid amount\
                                                       of team points')])
    mar_place = IntegerField('MAR Place',
                             validators=[Optional(),
                                         NumberRange(min=1,
                                                     max=3,
                                                     message='Invalid MAR\
                                                     place!')])
    mar_points = IntegerField('MAR Points',
                              validators=[Optional(),
                                          NumberRange(min=0,
                                                      max=3,
                                                      message='Invalid MAR\
                                                      points!')])
    point_prime = BooleanField('Point Prime', validators=[Optional()])
    dnf = BooleanField('DNF', validators=[Optional()])
    dns = BooleanField('DNS', validators=[Optional()])
    relegated = BooleanField('Relegated', validators=[Optional()])
    disqualified = BooleanField('Disqualified', validators=[Optional()])
    points_dropped = BooleanField('Points Dropped', validators=[Optional()])

    def __init__(self, race, *args, **kwargs):
        super(ParticipantForm, self).__init__(*args, **kwargs)
        self.race = race

    def validate_name(self, field):
        if Racer.query.filter_by(name=field.data).first() is None:
            raise ValidationError('Racer does not exist!')

    def validate_team_name(self, field):
        if Team.query.filter_by(name=field.data).first() is None:
            raise ValidationError('Team does not exist!')

class ParticipantAddForm(ParticipantForm):
    submit = SubmitField('Add')
    submit_another = SubmitField('Add + add another')

class ParticipantEditForm(ParticipantForm):
    submit = SubmitField('Save')

class PrimeForm(FlaskForm):
    name = StringField('Prime', validators=[Required()])

class PrimeAddForm(PrimeForm):
    participant_id = SelectField(u'Racer', coerce=int, validators=[Required()])
    submit = SubmitField('Add')

class PrimeEditForm(PrimeForm):
    submit = SubmitField('Save')

class RaceMarshalForm(FlaskForm):
    marshal_id = SelectField(u'Marshal', coerce=int, validators=[Required()])

class RaceMarshalAddForm(RaceMarshalForm):
    submit = SubmitField('Add')

class RaceOfficialForm(FlaskForm):
    official_id = SelectField(u'Official', coerce=int, validators=[Required()])

class RaceOfficialAddForm(RaceOfficialForm):
    submit = SubmitField('Add')


class AttachmentForm(FlaskForm):
    description = StringField('Description', validators=[Required()])

class AttachmentAddForm(AttachmentForm):
    attachment = FileField(validators=[FileRequired()])
    submit = SubmitField('Upload')

class AttachmentEditForm(AttachmentForm):
    submit = SubmitField('Save')
