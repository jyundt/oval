import logging
from flask_login import current_user
from flask import request

class ContextFilter(logging.Filter):
    def filter(self, log_record):
        log_record.blueprint = request.blueprint
        log_record.ip = request.environ.get("REMOTE_ADDR")
        if current_user.is_anonymous:
            log_record.admin_id = -1
            log_record.admin_username = 'Anonymous'
        else:
            log_record.admin_id = current_user.id
            log_record.admin_username = current_user.username

        return True
