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
    race_class_id = RaceClass.query.filter_by(name='C').first().id

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

@main.route('/race_class/')
def race_class():
    race_classes = RaceClass.query.order_by(RaceClass.name).all()
    return render_template('race_class.html', race_classes=race_classes)


@main.route('/race_class/<int:id>')
def race_class_details(id):
    race_class = RaceClass.query.get_or_404(id)

    return render_template('race_class_details.html', race_class=race_class)

@main.route('/race_class/add/', methods=['GET', 'POST'])
def race_class_add():
    form=RaceClassAddForm()
    if form.validate_on_submit():
        race_class_name = form.race_class_name.data
        race_class_id = form.race_class_id.data
        race_class=RaceClass(id=race_class_id,name=race_class_name)
        db.session.add(race_class)
        db.session.commit()
        flash('Race type ' + race_class.name + ' created!')
        return redirect(url_for('main.race_class'))


    return render_template('add.html',form=form,type='race class')

@main.route('/race_class/edit/<int:id>', methods=['GET', 'POST'])
def race_class_edit(id):
    race_class = RaceClass.query.get_or_404(id)
    form=RaceClassEditForm()
    
    if form.validate_on_submit():
        race_class_name = form.race_class_name.data
        race_class.name = race_class_name
        db.session.commit()
        flash('Race type ' + race_class.name + ' updated!')
        return redirect(url_for('main.race_class'))
        
    form.race_class_name.data = race_class.name
    return render_template('edit.html',
                           item=race_class,form=form,type='race class')

@main.route('/race_class/delete/<int:id>', methods=['POST'])
def race_class_delete(id):
    race_class = RaceClass.query.get_or_404(id)
    flash('Race type ' + race_class.name + ' deleted!')
    db.session.delete(race_class)
    db.session.commit()
    return redirect(url_for('main.race_class'))
