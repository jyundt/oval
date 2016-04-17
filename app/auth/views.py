from flask import render_template, redirect, request, url_for, flash, \
                  abort
from . import auth
from .forms import LoginForm, AdminAddForm, AdminEditForm,\
                   ChangePasswordForm,ResetPasswordForm,\
                   ResetPasswordRequestForm
from ..models import Admin
from flask_login import logout_user, login_required, login_user,\
                        current_user
from .. import db
from ..email import send_email

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

@auth.route('/change-password/', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            #db.session.add(current_user)
            current_user.password = form.password.data
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset/', methods=['GET', 'POST'])
def reset_password():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin:
             token = admin.generate_reset_token()
             send_email(admin.email, 'Reset Your Password',
                        'email/reset_password',
                        admin=admin, token=token,
                        next=request.args.get('next'))
        flash('An email with instructions to reset your password has been\
              sent to you.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>/', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin is None:
            #I dont think we should ever be in this?
            return redirect(url_for('main.index'))
        if admin.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Email address does not match password reset token!')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)
