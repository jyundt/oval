#Global-ish configuration settings
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '594a44b992b3ed67752f7e9807dd4daa'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #BOOTSTRAP_SERVE_LOCAL = True
    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SUBJECT_PREFIX = os.environ.get('MAIL_SUBJECT_PREFIX') or 'The_Oval_DEV'
    MAIL_SENDER = 'noreply@theoval.us'
    MAIL_FEEDBACK_ADDRESS = 'feedback@theoval.us'
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID') or 'UA-76360864-1'
    STRAVA_API_TOKEN = os.environ.get('STRAVA_API_TOKEN')
    STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
    STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
    SLACK_OAUTH_API_TOKEN = os.environ.get('SLACK_OAUTH_API_TOKEN')
    SLACK_OAUTH_API_TOKEN = os.environ.get('SLACK_OAUTH_API_TOKEN')
    DISQUS_ID = os.environ.get('DISQUS_ID') or 'the-oval-dev'
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_BUCKET = os.environ.get('S3_BUCKET')
    AUDIT_LOG = 'audit.log'
    MAX_CONTENT_LENGTH = 1024*1024*20

    @staticmethod
    def init_app(app):
        pass

class PostgresConfig(Config):
    SQLALCHEMY_DATABASE_USER = os.environ.get('DB_USER') or 'postgres'
    SQLALCHEMY_DATABASE_HOST = os.environ.get('DB_HOST') or 'localhost'
    SQLALCHEMY_DATABASE_PORT = os.environ.get('DB_PORT') or '5432'
    SQLALCHEMY_DATABASE_NAME = os.environ.get('DB_NAME') or 'oval'
    if os.environ.get('DB_PASS'):
        SQLALCHEMY_DATABASE_PASSWORD = os.environ.get('DB_PASS')
        SQLALCHEMY_DATABASE_URI = 'postgresql://' + SQLALCHEMY_DATABASE_USER + \
        ':' + SQLALCHEMY_DATABASE_PASSWORD + '@' + SQLALCHEMY_DATABASE_HOST + \
        ':' + SQLALCHEMY_DATABASE_PORT + '/' + SQLALCHEMY_DATABASE_NAME 
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://' + SQLALCHEMY_DATABASE_USER + \
        '@' + SQLALCHEMY_DATABASE_HOST + ':' + SQLALCHEMY_DATABASE_PORT + '/' + \
        SQLALCHEMY_DATABASE_NAME

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        import logging
        from app.log import ContextFilter
        from logging import Formatter
        from logging.handlers import SMTPHandler, RotatingFileHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()

        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.MAIL_FEEDBACK_ADDRESS],
            subject=cls.MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

        context_provider = ContextFilter()
        app.logger.addFilter(context_provider)
        audit_log_handler = RotatingFileHandler(cls.AUDIT_LOG, maxBytes=131072,
                                                backupCount=5)
        audit_log_handler.setLevel(logging.INFO)
        audit_log_handler.setFormatter(Formatter('%(asctime)s [%(levelname)s] %(ip)s %(admin_username)s[%(admin_id)d]: %(blueprint)s-%(funcName)s %(message)s'))
        app.logger.addHandler(audit_log_handler)

        app.logger.setLevel(logging.INFO) 

config = {
    'postgres': PostgresConfig,
	'default': PostgresConfig
}
