from flask import render_template, redirect, request, url_for, flash, abort
from . import auth
from .forms import LoginForm, AdminAddForm
from ..models import Admin
from flask_login import logout_user, login_required, login_user
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

@auth.route('/admin/add/', methods=['GET', 'POST'])
def admin_add():
    form = AdminAddForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        admin = Admin(email=email,username=username,password=password)
        db.session.add(admin)
        flash ('Admin ' + username + ' added!')
        return redirect(url_for('auth.login'))

    return render_template('add.html', form=form, type='admin')

