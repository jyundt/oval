from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import login_manager
from flask import current_app, request

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
    races = db.relationship('Race', cascade='all,delete', backref='race_class')
    

    def __repr__(self):
        return '<RaceClass %r>' % self.name

class Racer(db.Model):
    __tablename__ = 'racer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    usac_license = db.Column(db.Integer, unique=True)
    birthdate = db.Column(db.Date)
    participants = db.relationship('Participant', cascade='all,delete', 
                                   backref='racer')

    def __repr__(self):
        return '<Racer %r>' % self.name


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    participants = db.relationship('Participant', backref='team')

    def __repr__(self):
        return '<Team %r>' % self.name

class Race(db.Model):
    __tablename__ = 'race'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('race_class.id'))
    duration = db.Column(db.Interval)
    slow_lap = db.Column(db.Interval)
    fast_lap = db.Column(db.Interval)
    average_lap = db.Column(db.Interval)
    weather = db.Column(db.String(200))
    usac_permit = db.Column(db.String(200))
    laps = db.Column(db.Integer)
    starters = db.Column(db.Integer)
    participants= db.relationship('Participant', cascade='all,delete',
                                   backref='race')
    officials = db.relationship('RaceOfficial', cascade='all,delete',
                                   backref='race')
    marshals = db.relationship('RaceMarshal', cascade='all,delete',
                                   backref='race')


    def __repr__(self):
        return '<Race %r>' % self.date

class Participant(db.Model):
    ___tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    racer_id = db.Column(db.Integer, db.ForeignKey('racer.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    primes = db.relationship('Prime', cascade='all,delete', 
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


class Admin(UserMixin, db.Model):
    __tablename = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True)
    username = db.Column(db.String(200), unique=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(200))


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


@login_manager.user_loader
def load_user(admin_id):
    return Admin.query.get(int(admin_id))

