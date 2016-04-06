from flask import render_template, session, redirect, url_for, current_app,\
                  flash, abort
from sqlalchemy import extract, desc
from .. import db
from ..models import Official,Marshal,RaceClass,Racer,Team,Race,\
    Participant,RaceOfficial,RaceMarshal,Prime
#from ..email import send_email
from . import main
from .forms import RaceClassAddForm, RaceClassEditForm, RacerForm, TeamAddForm,\
                   RaceEditForm, ParticipantForm, TeamEditForm, RaceAddForm,\
                   ParticipantAddForm, ParticipantEditForm, PrimeAddForm,\
                   PrimeEditForm
from datetime import timedelta,datetime
from flask_login import login_required


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
            print participant.place
            print participant.points
           
            
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


@main.route('/race_class/<int:id>/')
def race_class_details(id):
    race_class = RaceClass.query.get_or_404(id)

    return render_template('race_class_details.html', race_class=race_class)

@main.route('/race_class/add/', methods=['GET', 'POST'])
def race_class_add():
    form=RaceClassAddForm()
    if form.validate_on_submit():
        name = form.name.data
        race_class=RaceClass(name=name)
        db.session.add(race_class)
        db.session.commit()
        flash('Race type ' + race_class.name + ' created!')
        return redirect(url_for('main.race_class'))


    return render_template('add.html',form=form,type='race class')

@main.route('/race_class/edit/<int:id>/', methods=['GET', 'POST'])
def race_class_edit(id):
    race_class = RaceClass.query.get_or_404(id)
    form=RaceClassEditForm(race_class)
    
    if form.validate_on_submit():
        name = form.name.data
        race_class.name = name
        db.session.commit()
        flash('Race type ' + race_class.name + ' updated!')
        return redirect(url_for('main.race_class'))
        
    form.name.data = race_class.name
    return render_template('edit.html',
                           item=race_class,form=form,type='race class')

@main.route('/race_class/delete/<int:id>/')
@login_required
def race_class_delete(id):
    race_class = RaceClass.query.get_or_404(id)
    db.session.delete(race_class)
    db.session.commit()
    flash('Race type ' + race_class.name + ' deleted!')
    return redirect(url_for('main.race_class'))

@main.route('/racer/')
def racer():
    racers = Racer.query.order_by(Racer.name).all()
    #racers = sorted(racers, key=lambda x: x.name.split()[1])
    
    return render_template('racer.html', racers=racers)


@main.route('/racer/<int:id>/')
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

@main.route('/racer/edit/<int:id>/', methods=['GET', 'POST'])
def racer_edit(id):
    racer = Racer.query.get_or_404(id)
    form=RacerForm()
    
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

@main.route('/racer/delete/<int:id>/')
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


@main.route('/team/<int:id>/')
def team_details(id):
    team = Team.query.get_or_404(id)

    return render_template('team_details.html', team=team)

@main.route('/team/add/', methods=['GET', 'POST'])
def team_add():
    form=TeamAddForm()
    if form.validate_on_submit():
        name = form.name.data
        team=Team(name=name)
        db.session.add(team)
        db.session.commit()
        flash('Team ' + team.name + ' created!')
        return redirect(url_for('main.team'))


    return render_template('add.html',form=form,type='team')

@main.route('/team/edit/<int:id>/', methods=['GET', 'POST'])
def team_edit(id):
    team = Team.query.get_or_404(id)
    form=TeamEditForm(team)
    
    if form.validate_on_submit():
        name = form.name.data
        team.name = name
        db.session.commit()
        flash('Team ' + team.name + ' updated!')
        return redirect(url_for('main.team'))
        
    form.name.data = team.name
    return render_template('edit.html', item=team,form=form,type='team')

@main.route('/team/delete/<int:id>/')
def team_delete(id):
    team = Team.query.get_or_404(id)
    db.session.delete(team)
    db.session.commit()
    flash('Team ' + team.name + ' deleted!')
    return redirect(url_for('main.team'))

@main.route('/race/')
def race():
    races = Race.query.order_by(desc(Race.date)).all()
    return render_template('race.html', races=races)

@main.route('/race/<int:id>/')
def race_details(id):
    race = Race.query.get_or_404(id)
    #I had to do this sort because jinja doesn't support lambas
    participants = sorted(race.participants, key=lambda x: (x.place is None, x.place))

    return render_template('race_details.html', race=race,
                           participants=participants)


@main.route('/race/add/', methods=['GET', 'POST'])
def race_add():
    form=RaceAddForm()
    form.class_id.choices = [(class_id.id, class_id.name) for class_id in
                            RaceClass.query.order_by('name')]
    if form.validate_on_submit():
        date = form.date.data
        if form.fast_lap.data is not None:
            fast_lap = timedelta(0, form.fast_lap.data.minute * 60
                                 + form.fast_lap.data.second)
        else:
            fast_lap = form.fast_lap.data
        
        if form.average_lap.data is not None:
            average_lap = timedelta(0, form.average_lap.data.minute * 60
                                    + form.average_lap.data.second)
        else:
            average_lap = form.average_lap.data
        if form.slow_lap.data is not None:
            slow_lap = timedelta(0, form.slow_lap.data.minute * 60
                                 + form.slow_lap.data.second)
        else:
            slow_lap = form.slow_lap.data

        weather = form.weather.data
        class_id = form.class_id.data
        usac_permit = form.usac_permit.data
        laps = form.laps.data

        race=Race(date=date,fast_lap=fast_lap, average_lap=average_lap,
                  slow_lap=slow_lap, weather=weather, class_id=class_id,
                  usac_permit=usac_permit, laps=laps)
        db.session.add(race)
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' created!')
        return redirect(url_for('main.race'))


    form.submit.label.text='Add'
    form.date.data=datetime.today()
    return render_template('add.html',form=form,type='race')

@main.route('/race/edit/<int:id>/', methods=['GET', 'POST'])
def race_edit(id):
    race = Race.query.get_or_404(id)
    form=RaceEditForm(race)
    form.class_id.choices = [(class_id.id, class_id.name) for class_id in
                            RaceClass.query.order_by('name')]
    
    if form.validate_on_submit():
        date = form.date.data
        if form.fast_lap.data is not None:
            fast_lap = timedelta(0, form.fast_lap.data.minute * 60
                                 + form.fast_lap.data.second)
        else:
            fast_lap = form.fast_lap.data
        
        if form.average_lap.data is not None:
            average_lap = timedelta(0, form.average_lap.data.minute * 60
                                    + form.average_lap.data.second)
        else:
            average_lap = form.average_lap.data
        if form.slow_lap.data is not None:
            slow_lap = timedelta(0, form.slow_lap.data.minute * 60
                                 + form.slow_lap.data.second)
        else:
            slow_lap = form.slow_lap.data

        weather = form.weather.data
        class_id = form.class_id.data
        usac_permit = form.usac_permit.data
        laps = form.laps.data

        race.date=date
        race.fast_lap=fast_lap
        race.average_lap=average_lap
        race.slow_lap=slow_lap
        race.weather = weather
        race.class_id=class_id
        race.usac_permit=usac_permit
        race.laps=laps
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' updated!')
        return redirect(url_for('main.race'))
        
    form.date.data = race.date
    form.class_id.data=race.class_id
    #This is so clunky :(
    if race.fast_lap is not None:
        form.fast_lap.data=datetime.strptime(str(race.fast_lap), '%H:%M:%S')
    if race.average_lap is not None:
        form.average_lap.data=datetime.strptime(str(race.average_lap),
                                                    '%H:%M:%S')
    if race.slow_lap is not None:
        form.slow_lap.data=datetime.strptime(str(race.slow_lap), '%H:%M:%S')
    form.weather.data=race.weather
    form.usac_permit.data=race.usac_permit
    form.laps.data=race.laps
    return render_template('edit.html', item=race,form=form,type='race')

@main.route('/race/delete/<int:id>/')
def race_delete(id):
    race = Race.query.get_or_404(id)
    db.session.delete(race)
    db.session.commit()
    flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' deleted!')
    return redirect(url_for('main.race'))

@main.route('/race/<int:id>/participant/add/', methods=['GET', 'POST'])
def race_add_participant(id):
    race = Race.query.get_or_404(id)
    form=ParticipantAddForm(race)
    form.team_id.choices = [(team_id.id, team_id.name) for team_id in 
                           Team.query.order_by('name')]
    form.team_id.choices.insert(0, (0, ''))
    if form.validate_on_submit():
        race_id = race.id
        racer_id=Racer.query.filter_by(name=form.name.data).first().id
        if form.team_id.data == 0:
            team_id=None
        else:
            team_id=form.team_id.data

        place = form.place.data
        points = form.points.data
        team_points = form.team_points.data
        mar_place = form.mar_place.data
        mar_points = form.mar_points.data
        point_prime = form.point_prime.data
        dnf = form.dnf.data
        dns = form.dns.data
        relegated = form.relegated.data        
        disqualified = form.disqualified.data        
        participant = Participant(racer_id=racer_id,team_id=team_id,
                                  points=points,team_points=team_points,
                                  mar_place=mar_place,mar_points=mar_points,
                                  point_prime=point_prime,dnf=dnf,dns=dns,
                                  relegated=relegated,
                                  disqualified=disqualified,
                                  race_id=race_id,place=place)
        db.session.add(participant)
        db.session.commit()
        return redirect(url_for('main.race_details',id=race.id))
        
    return render_template('add.html',form=form,type='participant')

    
@main.route('/race/<int:race_id>/participant/edit/<int:participant_id>', methods=['GET', 'POST'])
def race_edit_participant(race_id,participant_id):
    race = Race.query.get_or_404(race_id)
    participant = Participant.query.get_or_404(participant_id)
    if participant.race_id != race_id:
        abort(404) 
    form=ParticipantEditForm(race)
    form.team_id.choices = [(team_id.id, team_id.name) for team_id in 
                           Team.query.order_by('name')]
    form.team_id.choices.insert(0, (0, ''))
    if form.validate_on_submit():
        race_id = race.id
        racer_id=Racer.query.filter_by(name=form.name.data).first().id
        if form.team_id.data == 0:
            team_id=None
        else:
            team_id=form.team_id.data

        place = form.place.data
        points = form.points.data
        team_points = form.team_points.data
        mar_place = form.mar_place.data
        mar_points = form.mar_points.data
        point_prime = form.point_prime.data
        dnf = form.dnf.data
        dns = form.dns.data
        relegated = form.relegated.data        
        disqualified = form.disqualified.data        
        participant.racer_id=racer_id 
        participant.team_id=team_id
        participant.place=place
        participant.points=points
        participant.team_points = team_points
        participant.mar_place = mar_place
        participant.mar_points= mar_points
        participant.point_prime = point_prime
        participant.dnf = dnf
        participant.dns = dns
        participant.relegated = relegated
        participant.disqualified = disqualified
        db.session.commit()
        return redirect(url_for('main.race_details',id=race.id))

    form.place.data = participant.place
    form.points.data = participant.points
    form.team_points.data = participant.team_points
    form.name.data = participant.racer.name
    form.mar_place.data = participant.mar_place
    form.mar_points.data = participant.mar_points
    form.point_prime.data = participant.point_prime
    form.dnf.data = participant.dnf
    form.dns.data = participant.dns
    form.relegated.data = participant.relegated
    form.disqualified.data = participant.disqualified
    if participant.team is not None:
        form.team_id.data = participant.team.id
        
    return render_template('edit.html', item=participant,form=form,
                           type='participant')

    
@main.route('/race/<int:race_id>/participant/delete/<int:participant_id>')
def race_delete_participant(race_id,participant_id):
    race = Race.query.get_or_404(race_id)
    participant = Participant.query.get_or_404(participant_id)
    if participant.race_id != race_id:
        abort(404) 
    db.session.delete(participant)
    flash('Racer ' + participant.racer.name + ' deleted from race!')
    return redirect(url_for('main.race_details',id=race.id))
    
@main.route('/race/<int:id>/prime/add/', methods=['GET', 'POST'])
def race_add_prime(id):
    race = Race.query.get_or_404(id)
    form=PrimeAddForm()
    form.participant_id.choices = [(participant_id.id, 
                                   participant_id.racer.name)
                                   for participant_id in 
                                   Race.query.get(id).participants]
    if form.validate_on_submit():
        participant_id = form.participant_id.data
        name = form.name.data
        prime=Prime(name=name,participant_id=participant_id)
        db.session.add(prime)
        db.session.commit()
        flash('Prime for ' + prime.participant.racer.name + ' added!')
        return redirect(url_for('main.race_details',id=race.id))
    return render_template('add.html',form=form,type='prime')

@main.route('/race/<int:race_id>/prime/edit/<int:prime_id>/', methods=['GET',
                                                              'POST'])
def race_edit_prime(race_id,prime_id):
    race = Race.query.get_or_404(race_id)
    prime = Prime.query.get_or_404(prime_id)
    if prime.participant.race.id != race_id:
        abort(404) 
    form=PrimeEditForm()
    if form.validate_on_submit():
        name = form.name.data
        prime.name = name
        db.session.commit()
        flash('Prime for ' + prime.participant.racer.name + ' updated!')
        return redirect(url_for('main.race_details',id=race.id))

    form.name.data = prime.name
    return render_template('edit.html',item=prime,form=form,type='prime')

@main.route('/race/<int:race_id>/prime/delete/<int:prime_id>')
def race_delete_prime(race_id,prime_id):
    race = Race.query.get_or_404(race_id)
    prime = Prime.query.get_or_404(prime_id)
    if prime.participant.race.id != race_id:
        abort(404) 
    db.session.delete(prime)
    flash('Prime for ' + prime.participant.racer.name + ' deleted from race!')
    return redirect(url_for('main.race_details',id=race.id))

@main.route('/test/')
@login_required
def test():
    return 'auth!'
