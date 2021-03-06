from datetime import timedelta, datetime, date

import pytz
from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import func, extract
from sqlalchemy.ext.hybrid import hybrid_property
from stravalib import Client
from werkzeug.security import generate_password_hash, check_password_hash

from . import db
from . import login_manager


class Official(db.Model):
    __tablename__ = 'official'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    races = db.relationship('RaceOfficial', cascade='all,delete',
                            backref='official')

    def __repr__(self):
        return '<Official %r>' % self.name

class Marshal(db.Model):
    __tablename__ = 'marshal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    races = db.relationship('RaceMarshal', cascade='all,delete',
                            backref='marshal')

    def __repr__(self):
        return '<Marshal %r>' % self.name

class RaceClass(db.Model):
    __tablename__ = 'race_class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    color = db.Column(db.String(8))
    races = db.relationship('Race', cascade='all,delete', backref='race_class')

    @staticmethod
    def points_races(year, category_id):
        races = Race.query.filter(extract('year', Race.date) == year)\
                          .join(RaceClass)\
                          .filter(RaceClass.id == category_id)\
                          .join(Participant)\
                          .filter(Participant.points > 0)\
                          .order_by(Race.date)\
                          .all()
        return races


    def __repr__(self):
        return '<RaceClass %r>' % self.name

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    races = db.relationship('Race', cascade='all,delete', backref='course')
    length_miles = db.Column(db.Float)
    is_default = db.Column(db.Boolean)

    def __repr__(self):
        return '<Course %r>' % self.name

class NotificationEmail(db.Model):
    __tablename__ = 'notificationemail'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(100))

    @property
    def name(self):
        return '%s|%s' % (self.email, self.description)

    def __repr__(self):
        return '<Email %r>' % self.name


class AcaMembership(db.Model):
    __tablename__ = 'aca_membership'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer)
    racer_id = db.Column(db.Integer, db.ForeignKey('racer.id', ondelete='CASCADE'))
    season_pass = db.Column(db.Boolean, nullable=False, default=False)
    paid = db.Column(db.Boolean, nullable=False, default=False)
    __table_args__ = (db.UniqueConstraint('racer_id', 'year', name='uniq_member_year'),)

    @property
    def name(self):
        racer_name = Racer.query.get(self.racer_id).name
        return '%s|%s' % (racer_name, self.year)

    def __repr__(self):
        return '<AcaMembership %r>' % self.name


class Racer(db.Model):
    __tablename__ = 'racer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    usac_license = db.Column(db.Integer, unique=True)
    strava_id = db.Column(db.Integer, unique=True)
    strava_access_token = db.Column(db.String(40), unique=True)
    _strava_profile_url = db.Column('strava_profile_url', db.String(200))
    _strava_email = db.Column('strava_email', db.String(200))
    strava_profile_last_fetch = db.Column(db.DateTime(timezone=True))
    birthdate = db.Column(db.Date)
    current_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    participants = db.relationship('Participant', cascade='all,delete',
                                   backref='racer')

    @property
    def strava_profile_url(self):
        if self.strava_access_token is None:
            return None

        if self.strava_profile_last_fetch is None or\
           (datetime.now(pytz.timezone('UTC')) -\
            self.strava_profile_last_fetch)\
           > timedelta(minutes=5):
            self.strava_profile_last_fetch = datetime.now(pytz.timezone('UTC'))
            strava_client = Client(self.strava_access_token)
            strava_athlete = strava_client.get_athlete()
            if strava_athlete.profile == 'avatar/athlete/large.png':
                self.strava_profile_url = None
            else:
                self.strava_profile_url = strava_athlete.profile

        return self._strava_profile_url

    @strava_profile_url.setter
    def strava_profile_url(self, url):
        self._strava_profile_url = url
        db.session.commit()

    @property
    def strava_email(self):
        if self.strava_access_token is None:
            return None

        if self.strava_profile_last_fetch is None or\
           (datetime.now(pytz.timezone('UTC')) -\
            self.strava_profile_last_fetch)\
           > timedelta(minutes=5):
            self.strava_profile_last_fetch = datetime.now(pytz.timezone('UTC'))
            strava_client = Client(self.strava_access_token)
            strava_athlete = strava_client.get_athlete()
            self.strava_email = strava_athlete.email

        return self._strava_email

    @strava_email.setter
    def strava_email(self, email):
        self._strava_email = email
        db.session.commit()

    def season_points(self, year, category_id):
        result = Participant.query.with_entities(func.sum(Participant.points))\
                                  .join(Race)\
                                  .filter(extract('year', Race.date) == year)\
                                  .join(RaceClass)\
                                  .filter(RaceClass.id == category_id)\
                                  .join(Racer)\
                                  .filter(Racer.name == self.name)\
                                  .first()
        if result[0]:
            points = int(result[0])
        else:
            points = 0
        return points

    def season_mar_points(self, year, category_id):
        result = Participant.query\
                            .with_entities(func.sum(Participant.mar_points))\
                            .join(Race)\
                            .filter(extract('year', Race.date) == year)\
                            .join(RaceClass)\
                            .filter(RaceClass.id == category_id)\
                            .join(Racer)\
                            .filter(Racer.name == self.name)\
                            .first()

        if result[0]:
            points = int(result[0])
        else:
            points = 0
        return points

    @hybrid_property
    def race_age(self):
        if self.birthdate:
            race_age = date.today().year - self.birthdate.year
            return race_age
        else:
            return None

    @hybrid_property
    def points_eligible(self):
        year = date.today().year
        member = AcaMembership.query.filter_by(racer_id=self.id, year=year)\
                                    .one_or_none()
        return member and member.paid

    def __repr__(self):
        return '<Racer %r>' % self.name


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    participants = db.relationship('Participant', backref='team')
    current_racers = db.relationship('Racer', backref='current_team')

    def __repr__(self):
        return '<Team %r>' % self.name

class Race(db.Model):
    __tablename__ = 'race'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('race_class.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    duration = db.Column(db.Interval)
    slow_lap = db.Column(db.Interval)
    fast_lap = db.Column(db.Interval)
    average_lap = db.Column(db.Interval)
    winning_time = db.Column(db.Interval)
    weather = db.Column(db.String(200))
    usac_permit = db.Column(db.String(200))
    laps = db.Column(db.Integer)
    starters = db.Column(db.Integer)
    notes = db.Column(db.Text)
    points_race = db.Column(db.Boolean, default=False)
    picnic_race = db.Column(db.Boolean, default=False)
    attachments = db.relationship('RaceAttachment', cascade='all, delete',\
                                  backref='race')
    participants = db.relationship('Participant', cascade='all,delete',\
                                   backref='race')
    officials = db.relationship('RaceOfficial', cascade='all,delete',\
                                   backref='race')
    marshals = db.relationship('RaceMarshal', cascade='all,delete',\
                                   backref='race')

    @property
    def name(self):
        return '%s|%s' % (self.date, self.race_class.name)

    def __repr__(self):
        return '<Race %r>' % self.name

class Participant(db.Model):
    ___tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    racer_id = db.Column(db.Integer, db.ForeignKey('racer.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    primes = db.relationship('Prime', cascade='all,delete',\
                             backref='participant')
    place = db.Column(db.Integer)
    points = db.Column(db.Integer)
    team_points = db.Column(db.Integer)
    mar_points = db.Column(db.Integer)
    mar_place = db.Column(db.Integer)
    point_prime = db.Column(db.Boolean, default=False)
    dnf = db.Column(db.Boolean, default=False)
    dns = db.Column(db.Boolean, default=False)
    relegated = db.Column(db.Boolean, default=False)
    disqualified = db.Column(db.Boolean, default=False)
    points_dropped = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return '<Participant %r>' % self.id


class RaceOfficial(db.Model):
    ___tablename__ = 'race_official'
    id = db.Column(db.Integer, primary_key=True)
    official_id = db.Column(db.Integer, db.ForeignKey('official.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))

    def __repr__(self):
        return '<RaceOfficial %r>' % self.id


class RaceMarshal(db.Model):
    ___tablename__ = 'race_marshal'
    id = db.Column(db.Integer, primary_key=True)
    marshal_id = db.Column(db.Integer, db.ForeignKey('marshal.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))

    def __repr__(self):
        return '<RaceMarshal %r>' % self.id

class Prime(db.Model):
    ___tablename__ = 'prime'
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
    name = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Prime %r>' % self.name

class RaceAttachment(db.Model):
    __tablename__ = 'race_attachment'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    description = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    mimetype = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return '<RaceAttachment %r' % self.id

class Admin(UserMixin, db.Model):
    __tablename = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    username = db.Column(db.String(200), unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    roles = db.relationship('Role', secondary='admin_role',\
                            backref='admin')

    @property
    def name(self):
        return '%s|%s' % (self.username, self.email)

    def has_role(self, *specified_role_names):
        #I took this from Flask-User because I didn't need the whole thing
        if hasattr(self, 'roles'):
            roles = self.roles
        else:
            return False

        user_role_names = [role.name for role in roles]
        for role_name in specified_role_names:
            if role_name in user_role_names:
                return True

        return False

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.commit()
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.commit()
        return True



    def __repr__(self):
        return '<Admin %r>' % self.username

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(200), unique=True)

    #admins = db.relationship('Admin', secondary='admin_role'
    #                                , cascade='all,delete'
    #                                , backref='role')
    #admins = db.relationship('Admin', secondary='admin_role',backref='role')
    #Unfortunately I couldn't add this backref because deleting a Role
    #or Admin would cause an sqlalchemy ORM issue.

    @staticmethod
    def insert_roles():
        roles = ['superadmin', 'official', 'moderator']
        for role in roles:
            if Role.query.filter_by(name=role).first() is None:
                db.session.add(Role(name=role))
                db.session.commit()


    def __repr__(self):
        return '<Role %r>' % self.name

class AdminRole(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    admin_id = db.Column(db.Integer(), db.ForeignKey('admin.id',\
                                                     ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id',\
                                                    ondelete='CASCADE'))

    def __repr__(self):
        return '<AdminRole %r>' % self.id


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))

