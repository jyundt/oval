from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, EqualTo
from ..models import Admin
from wtforms import ValidationError

class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1,200)])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class AdminForm(Form):
    email = StringField('Email', validators=[Required(), Email()])
    username = StringField('Username', validators=[Required(), Length(1,200)])
    password = PasswordField('Password', validators=[Required(),
                             EqualTo('password2', message='Passwords do not match!')])
    password2 = PasswordField('Confirm password', validators=[Required()])

    def validate_email(self, field):
        if Admin.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered!')

    def validate_username(self, field):
        if Admin.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use!')


    
class AdminAddForm(AdminForm):
    submit = SubmitField('Add')

class AdminEditForm(AdminForm):
    submit = SubmitField('Save')

    def __init__(self, admin, *args, **kwargs):
        super(AdminEditForm, self).__init__(*args, **kwargs)
        self.admin = admin

    def validate_username(self, field):
        if field.data != self.admin.username and \
           Admin.query.filter(Admin.username.ilike(field.data)).first():
            raise ValidationError('Username already in use!')

    def validate_email(self, field):
        if field.data != self.admin.email and \
           Admin.query.filter(Admin.email.ilike(field.data)).first():
            raise ValidationError('Email already in use!')
    
           
