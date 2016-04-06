from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, EqualTo
from ..models import Admin

class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1,200)])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class AdminAddForm(Form):
    email = StringField('Email', validators=[Required(), Email()])
    username = StringField('Username', validators=[Required(), Length(1,200)])
    password = PasswordField('Password', validators=[Required(),
                             EqualTo('password2', message='Passwords do not match!')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Add')

    def validate_email(self, field):
        if Admin.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered!')

    def validate_username(self, field):
        if Admin.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use!')


    
