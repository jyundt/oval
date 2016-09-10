from flask_wtf import Form
from wtforms import BooleanField, DecimalField, StringField, SubmitField
from wtforms import ValidationError
from wtforms.validators import Optional, DataRequired
from ..models import Course


class CourseForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    length_miles = DecimalField('Lap length (miles)', validators=[Optional()])
    is_default = BooleanField('Default')


class CourseEditForm(CourseForm):
    submit = SubmitField('Save')

    def __init__(self, course, *args, **kwargs):
        super(CourseEditForm, self).__init__(*args, **kwargs)
        self.course = course

    def validate_name(self, field):
        if field.data != self.course.name and \
           Course.query.filter(Course.name.ilike(field.data)).first():
            raise ValidationError('Course type name already in use.')


class CourseAddForm(CourseForm):
    submit = SubmitField('Add')

    def validate_name(self, field):
        if Course.query.filter(Course.name.ilike(field.data)).first():
            raise ValidationError('Course type name already in use.')
