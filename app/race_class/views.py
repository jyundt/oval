from flask import render_template, redirect, url_for, flash, current_app
from .. import db
from ..models import RaceClass
from . import race_class
from .forms import RaceClassAddForm, RaceClassEditForm
from flask_login import current_user
from ..decorators import roles_accepted

@race_class.route('/')
@roles_accepted('official')
def index():
    race_classes = RaceClass.query.order_by(RaceClass.name).all()
    return render_template('race_class/index.html', race_classes=race_classes)


@race_class.route('/<int:id>/')
@roles_accepted('official')
def details(id):
    race_class = RaceClass.query.get_or_404(id)
    return render_template('race_class/details.html', race_class=race_class)

@race_class.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add():
    form = RaceClassAddForm()
    if form.validate_on_submit():
        name = form.name.data
        color = form.color.data
        race_class = RaceClass(name=name, color=color)
        db.session.add(race_class)
        db.session.commit()
        flash('Race type ' + race_class.name + ' created!')
        current_app.logger.info('%s[%d]', race_class.name, race_class.id)
        return redirect(url_for('race_class.index'))

    return render_template('add.html', form=form, type='race class')

@race_class.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
def edit(id):
    race_class = RaceClass.query.get_or_404(id)
    form = RaceClassEditForm(race_class)
    if form.validate_on_submit():
        name = form.name.data
        race_class.name = name
        color = form.color.data
        race_class.color = color
        db.session.commit()
        flash('Race type ' + race_class.name + ' updated!')
        current_app.logger.info('%s[%d]', race_class.name, race_class.id)
        return redirect(url_for('race_class.details',
                                id=race_class.id))
    form.name.data = race_class.name
    form.color.data = race_class.color
    return render_template('edit.html',
                           item=race_class, form=form, type='race class')

@race_class.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    race_class = RaceClass.query.get_or_404(id)
    current_app.logger.info('%s[%d]', race_class.name, race_class.id)
    db.session.delete(race_class)
    db.session.commit()
    flash('Race type ' + race_class.name + ' deleted!')
    return redirect(url_for('race_class.index'))
