from . import db

class Official(db.Model):
    __tablename__ = 'official'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)

    def __repr__(self):
        return '<Official %r>' % self.name

class Marshal(db.Model):
    __tablename__ = 'marshal'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)

    def __repr__(self):
        return '<Marshal %r>' % self.name

class RaceClass(db.Model):
    __tablename__ = 'race_class'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), unique=True)

    def __repr__(self):
        return '<RaceClass %r>' % self.name

class Racer(db.Model):
    __tablename__ = 'racer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    usac_license = db.Column(db.Integer, unique=True)
    birthdate = db.Column(db.Date)

    def __repr__(self):
        return '<Racer %r>' % self.name


class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)

    def __repr__(self):
        return '<Racer %r>' % self.name

class Race(db.Model):
    __tablename__ = 'race'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('race_class.id'))

    def __repr__(self):
        return '<Racer %r>' % self.name
