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
    #return '<h1>Found race for %s</h1>' % race.date
    return render_template('results/race.html',race=race)
    
        

@results.route('/racer/<int:id>')
def racer_results(id):
    #form = RaceResultsForm()
    #return render_template('results/race.html', form=form)
    racer = Racer.query.get_or_404(id)
    #return '<h1>Found race for %s</h1>' % race.date
    return render_template('results/racer.html',racer=racer)
    
        

