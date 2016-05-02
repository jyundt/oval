from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Required
from ..models import Marshal

class MarshalForm(Form):
    name = StringField('Name', validators=[Required()])

class MarshalEditForm(MarshalForm):
    submit = SubmitField('Save')

    def __init__(self, marshal, *args, **kwargs):
        super(MarshalEditForm, self).__init__(*args, **kwargs)
        self.marshal = marshal

    def validate_name(self, field):
        if field.data != self.marshal.name and \
           Marshal.query.filter(Marshal.name.ilike(field.data)).first():
            raise ValidationError('Marshal already exists!.')

class MarshalAddForm(MarshalForm):
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Marshal.query.filter(Marshal.name.ilike(field.data)).first():
            raise ValidationError('Marshal already exists!.')
