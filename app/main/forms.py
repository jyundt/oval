from flask_wtf import Form
from wtforms import StringField, SubmitField, SelectField,\
                    TextAreaField
from wtforms.validators import Required, Email

class FeedbackForm(Form):
    name = StringField('Name', validators=[Required()])
    replyaddress = StringField('Email Address',
                               validators=[Required(), Email()])
    subject = StringField('Subject', validators=[Required()])
    feedback = TextAreaField('Feedback', validators=[Required()])
    submit = SubmitField('Send')
