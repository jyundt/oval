from flask import render_template, redirect, url_for, flash
from .. import db
from ..models import Marshal
from . import marshal
from .forms import MarshalAddForm, MarshalEditForm
from ..decorators import roles_accepted

@marshal.route('/')
@roles_accepted('official')
def index():
    marshals = Marshal.query.order_by(Marshal.name).all()
    return render_template('marshal/index.html', marshals=marshals)

@marshal.route('/<int:id>/')
@roles_accepted('official')
def details(id):
    marshal = Marshal.query.get_or_404(id)

    return render_template('marshal/details.html', marshal=marshal)

@marshal.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add():
    form = MarshalAddForm()
    if form.validate_on_submit():
        name = form.name.data
        marshal = Marshal(name=name)
        db.session.add(marshal)
        db.session.commit()
        flash('Marshal ' + marshal.name + ' created!')
        return redirect(url_for('marshal.index'))

    return render_template('add.html', form=form, type='marshal')

@marshal.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
def edit(id):
    marshal = Marshal.query.get_or_404(id)
    form = MarshalEditForm(marshal)

    if form.validate_on_submit():
        name = form.name.data
        marshal.name = name
        db.session.commit()
        flash('Marshal ' + marshal.name + ' updated!')
        return redirect(url_for('marshal.index'))

    form.name.data = marshal.name
    return render_template('edit.html',
                           item=marshal, form=form, type='marshal')

@marshal.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    marshal = Marshal.query.get_or_404(id)
    db.session.delete(marshal)
    db.session.commit()
    flash('Marshal ' + marshal.name + ' deleted!')
    return redirect(url_for('marshal.index'))
