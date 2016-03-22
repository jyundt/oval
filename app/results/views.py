from flask import render_template, redirect, request, url_for, flash
from . import results
from .. import db
from .forms import RaceResultsForm

@results.route('/race')
def race_results():
    form = RaceResultsForm()
    return render_template('results/race.html', form=form)
        

