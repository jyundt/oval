from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_moment import Moment
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
moment = Moment()
login_manager = LoginManager()
login_manager.session_protection = 'basic'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .race_class import race_class as race_class_blueprint
    app.register_blueprint(race_class_blueprint, url_prefix='/race_class')

    from .racer import racer as racer_blueprint
    app.register_blueprint(racer_blueprint, url_prefix='/racer')

    from .team import team as team_blueprint
    app.register_blueprint(team_blueprint, url_prefix='/team')

    from .race import race as race_blueprint
    app.register_blueprint(race_blueprint, url_prefix='/race')

    from .marshal import marshal as marshal_blueprint
    app.register_blueprint(marshal_blueprint, url_prefix='/marshal')

    from .official import official as official_blueprint
    app.register_blueprint(official_blueprint, url_prefix='/official')

    from .course import course as course_blueprint 
    app.register_blueprint(course_blueprint, url_prefix='/course')

    return app
