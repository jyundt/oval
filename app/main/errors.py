import traceback
import StringIO
import socket
from slackclient import SlackClient
from flask import render_template, request, current_app
from datetime import datetime
from . import main

@main.app_errorhandler(400)
def page_not_found(e):
    return render_template('400.html'), 400

@main.app_errorhandler(403)
def page_not_found(e):
    return render_template('403.html'), 403

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(405)
def method_not_allowed(e):
    return render_template('405.html'), 405

@main.app_errorhandler(413)
def file_too_large(e):
    return render_template('413.html'), 413

@main.app_errorhandler(500)
def internal_server_error(e):
    token = current_app.config['SLACK_OAUTH_API_TOKEN']
    sc = SlackClient(token)
    tb = StringIO.StringIO()
    traceback.print_exc(None,tb)
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hostname = socket.gethostname()
    message = "%s - %s[%s] - ERROR - %s" % (date, hostname, request.path, e)
    sc.api_call("files.upload", channels="#ops", content=tb.getvalue(), initial_comment=message, filename="traceback.txt")
    tb.close()
    return render_template('500.html'), 500

