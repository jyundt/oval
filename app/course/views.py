from flask import render_template, redirect, url_for, flash, current_app
from .. import db
from ..models import Course
from . import course
from .forms import CourseAddForm, CourseEditForm
from flask_login import current_user
from ..decorators import roles_accepted

@course.route('/')
def index():
    courses = Course.query.order_by(Course.name).all()
    return render_template('course/index.html', courses=courses)


@course.route('/<int:id>/')
def details(id):
    course = Course.query.get_or_404(id)
    return render_template('course/details.html', course=course)

@course.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add():
    form = CourseAddForm()
    if form.validate_on_submit():
        name = form.name.data
        course = Course(name=name)
        db.session.add(course)
        db.session.commit()
        flash('Course type ' + course.name + ' created!')
        current_app.logger.info('%s[%d]', course.name, course.id)
        return redirect(url_for('course.index'))

    return render_template('add.html', form=form, type='course')

@course.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
def edit(id):
    course = Course.query.get_or_404(id)
    form = CourseEditForm(course)
    if form.validate_on_submit():
        name = form.name.data
        course.name = name
        db.session.commit()
        flash('Course type ' + course.name + ' updated!')
        current_app.logger.info('%s[%d]', course.name, course.id)
        return redirect(url_for('course.details',
                                id=course.id))
    form.name.data = course.name
    return render_template('edit.html',
                           item=course, form=form, type='course')

@course.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    course = Course.query.get_or_404(id)
    current_app.logger.info('%s[%d]', course.name, course.id)
    db.session.delete(course)
    db.session.commit()
    flash('Course type ' + course.name + ' deleted!')
    return redirect(url_for('course.index'))
