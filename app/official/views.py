from flask import render_template, redirect, url_for, flash, current_app
from .. import db
from ..models import Official
from . import official
from .forms import OfficialAddForm, OfficialEditForm
from ..decorators import roles_accepted

@official.route('/')
@roles_accepted('official')
def index():
    officials = Official.query.order_by(Official.name).all()
    return render_template('official/index.html', officials=officials)

@official.route('/<int:id>/')
@roles_accepted('official')
def details(id):
    official = Official.query.get_or_404(id)

    return render_template('official/details.html', official=official)

@official.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add():
    form = OfficialAddForm()
    if form.validate_on_submit():
        name = form.name.data
        official = Official(name=name)
        db.session.add(official)
        db.session.commit()
        flash('Official ' + official.name + ' created!')
        current_app.logger.info('%s[%d]', official.name, official.id)
        return redirect(url_for('official.index'))

    return render_template('add.html', form=form, type='official')

@official.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
def edit(id):
    official = Official.query.get_or_404(id)
    form = OfficialEditForm(official)

    if form.validate_on_submit():
        name = form.name.data
        official.name = name
        db.session.commit()
        flash('Official ' + official.name + ' updated!')
        current_app.logger.info('%s[%d]', official.name, official.id)
        return redirect(url_for('official.index'))

    form.name.data = official.name
    return render_template('edit.html',
                           item=official, form=form, type='official')

@official.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    official = Official.query.get_or_404(id)
    current_app.logger.info('%s[%d]', official.name, official.id)
    db.session.delete(official)
    db.session.commit()
    flash('Official ' + official.name + ' deleted!')
    return redirect(url_for('official.index'))
