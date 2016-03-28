from . import db

class Official(db.Model):
    __tablename__ = 'official'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    races = db.relationship('RaceOfficial', backref='official')

    def __repr__(self):
        return '<Official %r>' % self.name

class Marshal(db.Model):
    __tablename__ = 'marshal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    races = db.relationship('RaceMarshal', backref='marshal')

    def __repr__(self):
        return '<Marshal %r>' % self.name

class RaceClass(db.Model):
    __tablename__ = 'race_class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    races = db.relationship('Race', backref='race_class')
    

    def __repr__(self):
        return '<RaceClass %r>' % self.name

class Racer(db.Model):
    __tablename__ = 'racer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    usac_license = db.Column(db.Integer, unique=True)
    birthdate = db.Column(db.Date)
    participants = db.relationship('Participant', backref='racer')

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
    participants= db.relationship('Participant', backref='race')
    officials = db.relationship('RaceOfficial', backref='race')
    marshals = db.relationship('RaceMarshal', backref='race')


    def __repr__(self):
        return '<Race %r>' % self.date

class Participant(db.Model):
    ___tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    racer_id = db.Column(db.Integer, db.ForeignKey('racer.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'))
    primes = db.relationship('Prime', backref='participant')
    #result = db.relationship('Result',backref='participant')
    result = db.relationship('Result',uselist=False,backref='participant')

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

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'))
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
        return '<Result %r>' % self.id
