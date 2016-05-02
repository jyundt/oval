from flask_wtf import Form
from wtforms import StringField, SubmitField, SelectField, RadioField,\
                    TextAreaField
from wtforms.validators import Required, Optional, Email

class StandingsSearchForm(Form):
    year = SelectField(u'Year', coerce=int, validators=[Required()])
    race_class_id = SelectField(u'Race Class', coerce=int,
                                validators=[Required()])
    standings_type = RadioField('Standings Type',
                                choices=[('individual', 'Individual'),
                                         ('team', 'Team'),
                                         ('mar', 'MAR')],
                                validators=[Required()],
                                default='individual')
    submit = SubmitField('Search')

class FeedbackForm(Form):
    name = StringField('Name', validators=[Required()])
    replyaddress = StringField('Email Address',
                               validators=[Required(), Email()])
    subject = StringField('Subject', validators=[Required()])
    feedback = TextAreaField('Feedback', validators=[Required()])
    submit = SubmitField('Send')
