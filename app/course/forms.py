from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Required
from ..models import Course

class CourseForm(Form):
    name = StringField('Name', validators=[Required()])

class CourseEditForm(CourseForm):
    submit = SubmitField('Save')

    def __init__(self, race_class, *args, **kwargs):
        super(CourseEditForm, self).__init__(*args, **kwargs)
        self.race_class = race_class

    def validate_name(self, field):
        if field.data != self.race_class.name and \
           Course.query.filter(Course.name.ilike(field.data)).first():
            raise ValidationError('Course type name already in use.')

class CourseAddForm(CourseForm):
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Course.query.filter(Course.name.ilike(field.data)).first():
            raise ValidationError('Course type name already in use.')

