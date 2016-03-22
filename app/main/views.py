from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import Official,Marshal,RaceClass,Racer,Team,Race,\
    Participant,RaceOfficial,RaceMarshal,Prime,Result
#from ..email import send_email
from . import main
#from .forms import NameForm


@main.route('/')
def index():
    return render_template('index.html')

@main.route('/standings')
def standings():
    seasons = []
    for race in Race.query.all():
        seasons.append(race.date.year)
    #print sorted(set(seasons))
    return render_template('standings.html', seasons=sorted(set(seasons)))
