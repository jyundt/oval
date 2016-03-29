from flask import render_template, session, redirect, url_for, current_app,flash
from sqlalchemy import extract
from .. import db
from ..models import Official,Marshal,RaceClass,Racer,Team,Race,\
    Participant,RaceOfficial,RaceMarshal,Prime,Result
#from ..email import send_email
from . import main
from .forms import RaceClassForm, RacerForm, TeamForm


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
    form=RaceClassForm()
    form.submit.label.text='Add'
    if form.validate_on_submit():
        name = form.name.data
        race_class=RaceClass(name=name)
        db.session.add(race_class)
        db.session.commit()
        flash('Race type ' + race_class.name + ' created!')
        return redirect(url_for('main.race_class'))


    return render_template('add.html',form=form,type='race class')

@main.route('/race_class/edit/<int:id>', methods=['GET', 'POST'])
def race_class_edit(id):
    race_class = RaceClass.query.get_or_404(id)
    form=RaceClassForm()
    form.submit.label.text='Save'
    
    if form.validate_on_submit():
        name = form.name.data
        race_class.name = name
        db.session.commit()
        flash('Race type ' + race_class.name + ' updated!')
        return redirect(url_for('main.race_class'))
        
    form.name.data = race_class.name
    return render_template('edit.html',
                           item=race_class,form=form,type='race class')

@main.route('/race_class/delete/<int:id>')
def race_class_delete(id):
    race_class = RaceClass.query.get_or_404(id)
    db.session.delete(race_class)
    db.session.commit()
    flash('Race type ' + race_class.name + ' deleted!')
    return redirect(url_for('main.race_class'))

@main.route('/racer/')
def racer():
    racers = Racer.query.order_by(Racer.name).all()
    return render_template('racer.html', racers=racers)


@main.route('/racer/<int:id>')
def racer_details(id):
    racer = Racer.query.get_or_404(id)

    return render_template('racer_details.html', racer=racer)

@main.route('/racer/add/', methods=['GET', 'POST'])
def racer_add():
    form=RacerForm()
    form.submit.label.text='Add'
    if form.validate_on_submit():
        name = form.name.data
        usac_license = form.usac_license.data
        birthdate = form.birthdate.data
        racer=Racer(name=name, usac_license=usac_license,birthdate=birthdate)
        db.session.add(racer)
        db.session.commit()
        flash('Racer ' + racer.name + ' created!')
        return redirect(url_for('main.racer'))


    return render_template('add.html',form=form,type='racer')

@main.route('/racer/edit/<int:id>', methods=['GET', 'POST'])
def racer_edit(id):
    racer = Racer.query.get_or_404(id)
    form=RacerForm()
    form.submit.label.text='Save'
    
    if form.validate_on_submit():
        name = form.name.data
        racer.name = name
        usac_license = form.usac_license.data
        racer.usac_license = usac_license
        birthdate = form.birthdate.data
        racer.birthdate = birthdate
        db.session.commit()
        flash('Racer ' + racer.name + ' updated!')
        return redirect(url_for('main.racer'))
        
    form.name.data = racer.name
    form.usac_license.data = racer.usac_license
    form.birthdate.data = racer.birthdate
    return render_template('edit.html',
                           item=racer,form=form,type='racer')

@main.route('/racer/delete/<int:id>')
def racer_delete(id):
    racer = Racer.query.get_or_404(id)
    db.session.delete(racer)
    db.session.commit()
    flash('Racer ' + racer.name + ' deleted!')
    return redirect(url_for('main.racer'))

@main.route('/team/')
def team():
    teams = Team.query.order_by(Team.name).all()
    return render_template('team.html', teams=teams)


@main.route('/team/<int:id>')
def team_details(id):
    team = Team.query.get_or_404(id)

    return render_template('team_details.html', team=team)

@main.route('/team/add/', methods=['GET', 'POST'])
def team_add():
    form=TeamForm()
    form.submit.label.text='Add'
    if form.validate_on_submit():
        name = form.name.data
        team=Team(name=name)
        db.session.add(team)
        db.session.commit()
        flash('Team ' + team.name + ' created!')
        return redirect(url_for('main.team'))


    return render_template('add.html',form=form,type='team')

@main.route('/team/edit/<int:id>', methods=['GET', 'POST'])
def team_edit(id):
    team = Team.query.get_or_404(id)
    form=TeamForm()
    form.submit.label.text='Save'
    
    if form.validate_on_submit():
        name = form.name.data
        team.name = name
        db.session.commit()
        flash('Team ' + team.name + ' updated!')
        return redirect(url_for('main.team'))
        
    form.name.data = team.name
    return render_template('edit.html', item=team,form=form,type='team')

@main.route('/team/delete/<int:id>')
def team_delete(id):
    team = Team.query.get_or_404(id)
    db.session.delete(team)
    db.session.commit()
    flash('Team ' + team.name + ' deleted!')
    return redirect(url_for('main.team'))
