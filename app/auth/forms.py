from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,\
                    SelectMultipleField
from wtforms.validators import Required, Length, Email, EqualTo, Optional
from ..models import Admin
from wtforms import ValidationError
from wtforms import widgets

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class LoginForm(Form):
    username = StringField('Username', validators=[Required(), Length(1,200)])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class AdminForm(Form):
    email = StringField('Email', validators=[Required(), Email()])
    username = StringField('Username', validators=[Required(), Length(1,200)])
    roles = SelectMultipleField('Roles', coerce=int, validators=[Optional()])

    #roles = MultiCheckboxField('Roles', coerce=int, validators=[Optional()])
    def validate_email(self, field):
        if Admin.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered!')

    def validate_username(self, field):
        if Admin.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use!')


    
class AdminAddForm(AdminForm):
    password = PasswordField('Password', validators=[Required(),
                             EqualTo('password2'
                                     ,message='Passwords do not match!')])
    password2 = PasswordField('Confirm password', validators=[Required()])

    submit = SubmitField('Add')

class AdminEditForm(AdminForm):
    password = PasswordField('Password', validators=[Optional(),
                             EqualTo('password2'
                                     ,message='Passwords do not match!')])
    password2 = PasswordField('Confirm password', validators=[Optional(),
                             EqualTo('password'
                                     ,message='Passwords do not match!')])
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
    
           

class ChangePasswordForm(Form):
    old_password = PasswordField('Old password',validators=[Required()])
    password = PasswordField('New password', 
                             validators=[Required(),EqualTo('password2',\
                                         message='Passwords do\
                                                  not match!')])
    password2 = PasswordField('Repeat new password',
                              validators=[Required()])
    submit = SubmitField('Update Password')
        

class ResetPasswordRequestForm(Form):
    email = StringField('Email', validators=[Required(), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(Form):
    email = StringField('Confirm Email', validators=[Required(), Length(1, 64),
                                             Email()])
    password = PasswordField('New Password', validators=[
        Required(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[Required()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if Admin.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeEmailForm(Form):
    email = StringField('New Email', validators=[Required(), Email()])
    password = PasswordField('Current Password', validators=[Required()])
    submit = SubmitField('Update Email Address')

    def validate_email(self,field):
        if Admin.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
