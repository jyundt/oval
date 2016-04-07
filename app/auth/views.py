from flask import render_template, redirect, request, url_for, flash, abort
from . import auth
from .forms import LoginForm, AdminAddForm, AdminEditForm
from ..models import Admin
from flask_login import logout_user, login_required, login_user, current_user
from .. import db

@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()    
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin is not None and admin.verify_password(form.password.data):
            login_user(admin, form.remember_me.data)
            next = request.args.get('next')
            return redirect(next or url_for('main.index'))
        flash('Invalid username or password!')

    return render_template('auth/login.html', form=form)

@auth.route('/logout/')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/admin/')
@login_required
def admin():
    admins = Admin.query.order_by(Admin.username).all()
    return render_template('auth/admin.html', admins=admins)

@auth.route('/admin/<int:id>')
@login_required
def admin_details(id):
    admin=Admin.query.get_or_404(id)
    return render_template('auth/admin_details.html', admin=admin)

@auth.route('/admin/add/', methods=['GET', 'POST'])
def admin_add():
    if not current_user.is_authenticated:
        abort(403)
    form = AdminAddForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        admin = Admin(email=email,username=username,password=password)
        db.session.add(admin)
        flash ('Admin ' + username + ' added!')
        return redirect(url_for('auth.admin'))

    return render_template('add.html', form=form, type='admin')

@auth.route('/admin/edit/<int:id>/', methods=['GET', 'POST'])
def admin_edit(id):
    if not current_user.is_authenticated:
        abort(403)
    admin = Admin.query.get_or_404(id)
    form=AdminEditForm(admin)
    
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        admin.email=email
        admin.username = username
        admin.password = password
        db.session.commit()
        flash('Admin ' + username + ' updated!')
        return redirect(url_for('auth.admin'))

    form.username.data = admin.username
    form.email.data = admin.email
    return render_template('edit.html', item=admin, form=form, type='admin')
    
    
@auth.route('/admin/delete/<int:id>/')
def admin_delete(id):
    if not current_user.is_authenticated:
        abort(403)
    admin= Admin.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    flash('Admin ' + admin.username + ' deleted!')
    return redirect(url_for('auth.admin'))
