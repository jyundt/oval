import datetime
import os
import subprocess
from flask import render_template, redirect, request, url_for, flash,\
                  current_app, make_response
from . import auth
from .forms import LoginForm, AdminAddForm, AdminEditForm,\
                   ChangePasswordForm, ResetPasswordForm,\
                   ResetPasswordRequestForm, ChangeEmailForm,\
                   NotificationEmailAddForm, NotificationEmailEditForm
from ..models import Admin, Role, AdminRole, NotificationEmail
from flask_login import logout_user, login_required, login_user,\
                        current_user
from .. import db
from ..email import send_email
from ..decorators import roles_accepted

@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin is not None and admin.verify_password(form.password.data):
            login_user(admin, form.remember_me.data)
            next = request.args.get('next')
            current_app.logger.info('')
            return redirect(next or url_for('main.index'))
        current_app.logger.warning('failed login attempt %s',
                                   form.username.data)
        flash('Invalid username or password!')

    return render_template('auth/login.html', form=form)

@auth.route('/logout/')
@login_required
def logout():
    current_app.logger.info('')
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/admin/')
@roles_accepted('superadmin')
def admin():
    admins = Admin.query.order_by(Admin.username).all()
    return render_template('auth/admin.html', admins=admins)

@auth.route('/admin/<int:id>')
@roles_accepted('superadmin')
def admin_details(id):
    admin = Admin.query.get_or_404(id)
    return render_template('auth/admin_details.html', admin=admin)

@auth.route('/admin/add/', methods=['GET', 'POST'])
@roles_accepted('superadmin')
def admin_add():
    form = AdminAddForm()
    form.roles.choices = [(role.id, role.name) for role in
                          Role.query.order_by('name')]
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data
        admin = Admin(email=email, username=username, password=password)
        db.session.add(admin)
        db.session.commit()
        if form.roles.data:
            for role_id in form.roles.data:
                role_name = Role.query.get(role_id).name
                if role_name not in [(role.name) for role in admin.roles]:
                    db.session.add(AdminRole(role_id=role_id,
                                             admin_id=admin.id))
        db.session.commit()
        flash('Admin ' + username + ' added!')
        current_app.logger.info('%s[%d]', admin.name, admin.id)
        return redirect(url_for('auth.admin'))

    return render_template('add.html', form=form, type='admin')

@auth.route('/admin/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('superadmin')
def admin_edit(id):
    admin = Admin.query.get_or_404(id)
    form = AdminEditForm(admin)
    form.roles.choices = [(role.id, role.name) for role in
                          Role.query.order_by('name')]

    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        if form.password.data != '':
            password = form.password.data
            admin.password = password

        admin.email = email
        admin.username = username
        if form.roles.data:
            for role_id in form.roles.data:
                role_name = Role.query.get(role_id).name
                if role_name not in [(role.name) for role in admin.roles]:
                    db.session.add(AdminRole(role_id=role_id,
                                             admin_id=admin.id))
            db.session.commit()
        for role in admin.roles:
            role_id = role.id
            admin_id = admin.id
            if role_id not in form.roles.data:
                db.session.delete(AdminRole.query\
                                           .filter_by(role_id=role_id)\
                                           .filter_by(admin_id=admin_id)\
                                           .first())
                db.session.commit()
        flash('Admin ' + username + ' updated!')
        current_app.logger.info('%s[%d]', admin.name, admin.id)
        return redirect(url_for('auth.admin_details', id=admin.id))

    form.username.data = admin.username
    form.email.data = admin.email
    form.roles.data = [(role.id) for  role in admin.roles]
    return render_template('edit.html', item=admin, form=form, type='admin')

@auth.route('/admin/delete/<int:id>/')
@roles_accepted('superadmin')
def admin_delete(id):
    admin = Admin.query.get_or_404(id)
    current_app.logger.info('%s[%d]', admin.name, admin.id)
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
            db.session.commit()
            flash('Your password has been updated.')
            current_app.logger.info('')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
            current_app.logger.warning('invalid password')
            return redirect(url_for('auth.change_password'))
    return render_template('auth/change_password.html', form=form)

@auth.route('/reset/', methods=['GET', 'POST'])
def reset_password_request():
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
        current_app.logger.info('%s', form.email.data)
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>/', methods=['GET', 'POST'])
def reset_password(token):
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
            current_app.logger.info('%s', admin.username)
            return redirect(url_for('auth.login'))
        else:
            flash('Email address does not match password reset token or\
                   token has expired!')
            current_app.logger.warning('bad/expired reset token %s',
                                       form.email.data)
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email/', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your new email address',
                       'email/change_email',
                       admin=current_user, token=token)
            flash('An email with instructions to confirm your new email\
                  address has been sent to you.')
            current_app.logger.info('')
            return redirect(url_for('main.index'))
        else:
            current_app.logger.warning('invalid password')
            flash('Invalid email or password.')
            return redirect(url_for('auth.change_email_request'))

    return render_template('auth/change_email.html', form=form)

@auth.route('/change-email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('Your email address has been updated.')
        current_app.logger.info('')
    else:
        current_app.logger.warning('bad/expired reset token %s',
                                   form.email.data)
        flash('Invalid requiest.')
    return redirect(url_for('main.index'))

@auth.route('/log/')
@login_required
@roles_accepted('superadmin')
def display_log():
    with open(current_app.config['AUDIT_LOG'], "r") as f:
        audit_log = f.read()

    return render_template("auth/log.html", audit_log=audit_log)

@auth.route('/email/')
@roles_accepted('superadmin')
def notificationemail():
    notificationemails = NotificationEmail.query\
                                          .order_by(NotificationEmail.email)\
                                          .all()
    return render_template('auth/email.html',\
                           notificationemails=notificationemails)

@auth.route('/email/add/', methods=['GET', 'POST'])
@roles_accepted('superadmin')
def notificationemail_add():
    form = NotificationEmailAddForm()
    if form.validate_on_submit():
        email = form.email.data
        description = form.description.data
        notificationemail = NotificationEmail(email=email,\
                                              description=description)
        db.session.add(notificationemail)
        db.session.commit()
        flash('Email ' + email + ' added!')
        current_app.logger.info('%s[%d]', notificationemail.name,\
                                notificationemail.id)
        return redirect(url_for('auth.notificationemail'))

    return render_template('add.html', form=form, type='email')

@auth.route('/email/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('superadmin')
def notificationemail_edit(id):
    notificationemail = NotificationEmail.query.get_or_404(id)
    form = NotificationEmailEditForm(notificationemail)
    if form.validate_on_submit():
        email = form.email.data
        description = form.description.data
        notificationemail.email = email
        notificationemail.description = description
        db.session.commit()
        flash('Email ' + email + ' updated!')
        current_app.logger.info('%s[%d]', notificationemail.name,\
                                notificationemail.id)
        return redirect(url_for('auth.notificationemail'))
    form.email.data = notificationemail.email
    form.description.data = notificationemail.description
    return render_template('edit.html', item=notificationemail,\
                           form=form, type='email')

@auth.route('/email/delete/<int:id>/')
@roles_accepted('superadmin')
def notificationemail_delete(id):
    notificationemail = NotificationEmail.query.get_or_404(id)
    current_app.logger.info('%s[%d]', notificationemail.name,\
                            notificationemail.id)
    db.session.delete(notificationemail)
    db.session.commit()
    flash('Email ' + notificationemail.email + ' deleted!')
    return redirect(url_for('auth.notificationemail'))

@auth.route('/download_db/')
@roles_accepted('superadmin')
def download_db():
    cmd = ['pg_dump', '-h', current_app.config['SQLALCHEMY_DATABASE_HOST'],
           '-U', current_app.config['SQLALCHEMY_DATABASE_USER'],
           '--clean', '--no-owner', '-t', 'public.*',
           current_app.config['SQLALCHEMY_DATABASE_NAME']]
    pgenv = os.environ.copy()
    if current_app.config.get('SQLALCHEMY_DATABASE_PASSWORD'):
        pgenv['PGPASSWORD'] = current_app.config['SQLALCHEMY_DATABASE_PASSWORD']
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE, env=pgenv)
    db_dump = p.communicate()[0]
    db_file='oval_db_{:%Y%m%d%H%M%S}.sql'.format(datetime.datetime.now())

    response = make_response(db_dump)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + db_file
                                               
    current_app.logger.info('')
    return response 
