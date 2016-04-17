from threading import Thread
from flask import current_app, render_template
from flask_mail import Message
from . import mail

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_feedback_email(name,replyaddress,subject,feedback):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'],
                  recipients=[app.config['MAIL_FEEDBACK_ADDRESS']],
                  reply_to=name + '<' + replyaddress + '>')
    msg.body = feedback
    msg.html = feedback
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'],
                  recipients=[to],
                  reply_to=app.config['MAIL_SENDER'])
    msg.body = render_template(template + ".txt", **kwargs)
    msg.html = render_template(template + ".html", **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
