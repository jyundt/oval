from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField,\
                    TextAreaField
from wtforms.validators import Required, Email

class FeedbackForm(FlaskForm):
    name = StringField('Name', validators=[Required()])
    replyaddress = StringField('Email Address',
                               validators=[Required(), Email()])
    subject = StringField('Subject', validators=[Required()])
    feedback = TextAreaField('Feedback', validators=[Required()])
    submit = SubmitField('Send')
