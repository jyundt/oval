from flask import render_template, redirect, request, url_for, flash
from . import results
from .. import db
from .forms import RaceResultsForm
from ..models import Race,Racer

@results.route('/race/<int:id>')
def race_results(id):
    #form = RaceResultsForm()
    #return render_template('results/race.html', form=form)
    race = Race.query.get_or_404(id)
    #return render_template('results/race.html',race=race)
    #Whoops, we need to sort the racers by race
    #I had to do this kludge so that "None" was moved to the end
    participants = sorted(race.participants, key=lambda x: (x.result.place is None, x.result.place))
    return render_template('results/race.html', participants=participants,
                                                race=race)
    
        

@results.route('/racer/<int:id>')
def racer_results(id):
    #form = RaceResultsForm()
    #return render_template('results/race.html', form=form)
    racer = Racer.query.get_or_404(id)
    #return '<h1>Found race for %s</h1>' % race.date
    return render_template('results/racer.html',racer=racer)
    
        

