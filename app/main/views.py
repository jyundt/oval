from flask import render_template, session, redirect, url_for, current_app,flash
from sqlalchemy import extract
from .. import db
from ..models import Official,Marshal,RaceClass,Racer,Team,Race,\
    Participant,RaceOfficial,RaceMarshal,Prime,Result
#from ..email import send_email
from . import main
from .forms import RaceClassAddForm, RaceClassEditForm


#The goal of this function is return a table for the current standings for
#a given season
#e.g. Place Name Team Points
def generate_standings(year,race_class):
    #This is clunky, but I need to get the class_id for this race class
    race_class_id = RaceClass.query.filter_by(description='C').first().id

    #Generate a list of races for us to calculate standings
    races = Race.query.filter(extract('year',Race.date)==2015,\
                              Race.class_id==race_class_id).all()    

    #I don't know of a better way of doing this, so I'm going to build a list 
    # of dicts (of racers) and just do a running subtotal

    rider_points = {}
    for race in races:
        for participant in race.participants:
            print participant.racer.name
            print participant.result.place
            print participant.result.points
           
            
    return races

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/standings')
def standings():
    races = generate_standings(2015,'C')
    seasons = []
    for race in Race.query.all():
        seasons.append(race.date.year)
    #return render_template('standings.html', seasons=sorted(set(seasons)))
    return render_template('standings.html', seasons=sorted(set(races)))

@main.route('/race_class/', methods=['GET', 'POST'])
def race_class():
    form = RaceClassAddForm()
    if form.validate_on_submit():
        if RaceClass.query.filter(RaceClass.description.ilike(
                                  form.race_class_description.data)).first():
            flash('Error: that race type already exists!')
        else:
            race_category=RaceClass(description=\
                                    form.race_class_description.data)
            db.session.add(race_category)
            db.session.commit()
        return redirect(url_for('main.race_class'))
    #I guess let's start by displaying the existing Race classe?
    race_classes = RaceClass.query.order_by(RaceClass.description).all()
    return render_template('race_class.html', race_classes=race_classes, form=form)


@main.route('/race_class/<int:id>')
def race_class_details(id):
    race_class = RaceClass.query.get_or_404(id)

    return render_template('race_class_details.html', race_class=race_class)

@main.route('/race_class/edit/<int:id>', methods=['GET', 'POST'])
@main.route('/race_class/edit/', defaults={'id': None}, methods=['GET', 'POST'])
def race_class_edit(id):
    form=RaceClassEditForm()
    if id != None:
        race_class = RaceClass.query.get_or_404(id)
    if form.validate_on_submit():
        failed = False
        if RaceClass.query.get(form.race_class_id.data):
            flash('Error: that race type DB ID already exists!')
            failed = True
        if RaceClass.query.filter(RaceClass.description.ilike(
                                  form.race_class_description.data)).first():
            flash('Error: that race type already exists!')
            failed = True

        if failed and id == None:
            return render_template('race_class_edit.html',form=form)
        elif failed:
            return render_template('race_class_edit.html',
                                   race_class=race_class,form=form)
        else:
            race_class=RaceClass(id=form.race_class_id.data,
                                 description=form.race_class_description.data)
            db.session.add(race_class)
            db.session.commit()
            return redirect(url_for('main.race_class'))
        
    if id != None:
        form.race_class_id.data = race_class.id
        form.race_class_description.data = race_class.description
        return render_template('race_class_edit.html',
                               race_class=race_class,form=form)
    else:
        form.submit.label.text='Add'
        return render_template('race_class_edit.html',form=form)
    #if form.validate_on_submit():
    #    if RaceClass.query.get(form.race_class_id.data).first():
    #        flash('Error: that race type DB ID already exists!')
