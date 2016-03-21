#Global-ish configuration settings
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '594a44b992b3ed67752f7e9807dd4daa'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    @staticmethod
    def init_app(app):
        pass

class PostgresConfig(Config):
    SQLALCHEMY_DATABASE_USER = os.environ.get('DB_USER') or 'postgres'
    SQLALCHEMY_DATABSE_HOST = os.environ.get('DB_HOST') or 'localhost'
    SQLALCHEMY_DATABSE_PORT = os.environ.get('DB_PORT') or '5432'
    SQLALCHEMY_DATABSE_NAME = os.environ.get('DB_NAME') or 'oval'
    if os.environ.get('DB_PASS'):
        SQLALCHEMY_DATABSE_PASSWORD = os.environ.get('DB_PASS')
        SQLALCHEMY_DATABASE_URI = 'postgresql://' + SQLALCHEMY_DATABASE_USER + \
        ':' + SQLALCHEMY_DATABSE_PASSWORD + '@' + SQLALCHEMY_DATABSE_HOST + \
        ':' + SQLALCHEMY_DATABSE_PORT + '/' + SQLALCHEMY_DATABSE_NAME 
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://' + SQLALCHEMY_DATABASE_USER + \
        '@' + SQLALCHEMY_DATABSE_HOST + ':' + SQLALCHEMY_DATABSE_PORT + '/' + \
        SQLALCHEMY_DATABSE_NAME


config = {
    'postgres': PostgresConfig,
	'default': PostgresConfig
}
