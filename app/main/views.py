import requests
import json
from flask import render_template, session, redirect, url_for, current_app,\
                  flash, abort, request, jsonify
from sqlalchemy import extract, desc, func, and_
from .. import db
from ..models import Official,Marshal,RaceClass,Racer,Team,Race,\
    Participant,RaceOfficial,RaceMarshal,Prime
from ..email import send_feedback_email
from . import main
from .forms import RaceClassAddForm, RaceClassEditForm, TeamAddForm,\
                   RaceEditForm, ParticipantForm, TeamEditForm, RaceAddForm,\
                   ParticipantAddForm, ParticipantEditForm, PrimeAddForm,\
                   PrimeEditForm, MarshalAddForm, MarshalEditForm,\
                   RaceMarshalAddForm, OfficialAddForm, OfficialEditForm,\
                   RaceOfficialAddForm, StandingsSearchForm,FeedbackForm,\
                   RacerAddForm, RacerEditForm,RacerAddToTeamForm,\
                   RacerSearchForm, RaceSearchForm
from datetime import timedelta,datetime
from flask_login import current_user, login_required

#The goal of this function is return a table for the current standings for
#a given season
#e.g. Place Name Team Points
def generate_standings(year,race_class_id,standings_type):
    if standings_type == 'team':
        results = Team.query.with_entities(Team.name, 
                                           func.sum(Participant.team_points),\
                                           Team.id)\
                            .join(Participant)\
                            .join(Race)\
                            .join(RaceClass)\
                            .group_by(Team.id)\
                            .filter(and_(Race.class_id==race_class_id,\
                                         extract('year',Race.date)==year))\
                            .having(func.sum(Participant.team_points) >0)\
                            .order_by(func.sum(Participant.team_points)\
                            .desc()).all()

    elif standings_type == 'individual':
        results = Racer.query.with_entities(Racer.name,
                                            func.sum(Participant.points),\
                                            Racer.id )\
                             .join(Participant)\
                             .join(Race)\
                             .join(RaceClass)\
                             .group_by(Racer.id)\
                             .filter(and_(Race.class_id==race_class_id,\
                                          extract('year',Race.date)==year))\
                             .having(func.sum(Participant.points) > 0)\
                             .order_by(func.sum(Participant.points)\
                             .desc()).all()

    elif standings_type == 'mar':
        results = Racer.query.with_entities(Racer.name,
                                            func.sum(Participant.mar_points),\
                                            Racer.id)\
                             .join(Participant)\
                             .join(Race)\
                             .join(RaceClass)\
                             .group_by(Racer.id)\
                             .filter(and_(Race.class_id==race_class_id,\
                                          extract('year',Race.date)==year))\
                             .having(func.sum(Participant.mar_points) > 0)\
                             .order_by(func.sum(Participant.mar_points)\
                             .desc()).all()
    else:
        results = None

    return results


    

@main.route('/')
def index():
    #Let's hard code the categories that we'd like to see on the front page
    categories=['A', 'B', 'C', 'Masters 40+/Women']
    races = []
    for category in categories:
        races.append(Race.query.join(RaceClass)
                                   .filter_by(name=category)
                                   .order_by(Race.date.desc())
                                   .first())
    return render_template('index.html',races=races)

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
    if not current_user.is_authenticated:
        abort(403)
    form=RaceClassAddForm()
    if form.validate_on_submit():
        name = form.name.data
        color = form.color.data
        race_class=RaceClass(name=name,color=color)
        db.session.add(race_class)
        db.session.commit()
        flash('Race type ' + race_class.name + ' created!')
        return redirect(url_for('main.race_class'))


    return render_template('add.html',form=form,type='race class')

@main.route('/race_class/edit/<int:id>/', methods=['GET', 'POST'])
def race_class_edit(id):
    if not current_user.is_authenticated:
        abort(403)
    race_class = RaceClass.query.get_or_404(id)
    form=RaceClassEditForm(race_class)
    
    if form.validate_on_submit():
        name = form.name.data
        race_class.name = name
        color = form.color.data
        race_class.color = color
        db.session.commit()
        flash('Race type ' + race_class.name + ' updated!')
        return redirect(url_for('main.race_class_details',
                                id=race_class.id))
        
    form.name.data = race_class.name
    form.color.data = race_class.color
    return render_template('edit.html',
                           item=race_class,form=form,type='race class')

@main.route('/race_class/delete/<int:id>/')
def race_class_delete(id):
    if not current_user.is_authenticated:
        abort(403)
    race_class = RaceClass.query.get_or_404(id)
    db.session.delete(race_class)
    db.session.commit()
    flash('Race type ' + race_class.name + ' deleted!')
    return redirect(url_for('main.race_class'))

@main.route('/racer/')
def racer():
    racers = Racer.query.order_by(Racer.name).all()
    return render_template('racer.html', racers=racers)

@main.route('/racer/search/', methods=['GET', 'POST'])
def racer_search():
    form=RacerSearchForm()
    form.name.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                         'autocomplete':'off',
                         'data-source':json.dumps([racer.name for racer in
                                                   Racer.query.all()])}

    if form.validate_on_submit():
        name = form.name.data      
        racers = Racer.query.filter(Racer.name.ilike('%'+name+'%')).all()
        if len(racers) == 1:
            racer=racers[0]
            return redirect(url_for('main.racer_details',id=racer.id))
        else:
            return render_template('racer_search.html',racers=racers,\
                                   form=form)
            
            

    return render_template('racer_search.html', racers=None,form=form)
    


@main.route('/racer/<int:id>/')
def racer_details(id):
    racer = Racer.query.get_or_404(id)
    teams = Team.query.join(Participant)\
                      .join(Racer)\
                      .filter_by(id=id)\
                      .join(Race)\
                      .order_by(Race.date.desc())\
                      .all()
    current_team=racer.current_team
    if current_team in teams:
        teams.remove(current_team)
    return render_template('racer_details.html', racer=racer,
                           current_team=current_team, teams=teams)

@main.route('/racer/add/', methods=['GET', 'POST'])
def racer_add():
    if not current_user.is_authenticated:
        abort(403)
    form=RacerAddForm()
    form.current_team.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                                 'autocomplete':'off',
                                 'data-source':json.dumps([team.name for team in
                                                          Team.query.all()])}
    if form.validate_on_submit():
        name = form.name.data
        usac_license = form.usac_license.data
        strava_id = form.strava_id.data
        birthdate = form.birthdate.data
        if form.current_team.data:
            current_team_id=Team.query.filter_by(name=form.current_team.data)\
                                      .first().id
        else:
            current_team_id=None
        racer=Racer(name=name, usac_license=usac_license,birthdate=birthdate,
                    current_team_id=current_team_id,
                    strava_id=strava_id)
        db.session.add(racer)
        db.session.commit()
        flash('Racer ' + racer.name + ' created!')
        return redirect(url_for('main.racer'))


    return render_template('add.html',form=form,type='racer')

@main.route('/racer/edit/<int:id>/', methods=['GET', 'POST'])
def racer_edit(id):
    if not current_user.is_authenticated:
        abort(403)
    racer = Racer.query.get_or_404(id)
    form=RacerEditForm(racer)
    form.current_team.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                                 'autocomplete':'off',
                                 'data-source':json.dumps([team.name for team in
                                                          Team.query.all()])}
    
    if form.validate_on_submit():
        name = form.name.data
        racer.name = name
        usac_license = form.usac_license.data
        racer.usac_license = usac_license
        birthdate = form.birthdate.data
        racer.birthdate = birthdate
        strava_id = form.strava_id.data
        racer.strava_id=strava_id
        if form.current_team.data:
            current_team_id=Team.query.filter_by(name=form.current_team.data)\
                                      .first().id
        else:
            current_team_id=None
        racer.current_team_id = current_team_id
        db.session.commit()
        flash('Racer ' + racer.name + ' updated!')
        return redirect(url_for('main.racer_details',id=racer.id))
        
    form.name.data = racer.name
    form.usac_license.data = racer.usac_license
    form.birthdate.data = racer.birthdate
    form.strava_id.data = racer.strava_id
    if racer.current_team_id:
        form.current_team.data = Team.query.get(racer.current_team_id).name
    return render_template('edit.html',
                           item=racer,form=form,type='racer')

@main.route('/racer/delete/<int:id>/')
def racer_delete(id):
    if not current_user.is_authenticated:
        abort(403)
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
    current_racers = team.current_racers
    results = Race.query.with_entities(Race.date,
                                       RaceClass.name,
                                       func.count(Racer.id),
                                       Race.id)\
                                       .join(Participant)\
                                       .join(Racer)\
                                       .join(Team,Team.id==Participant.team_id)\
                                       .join(RaceClass)\
                                       .filter(Team.id==team.id)\
                                       .group_by(Race.date,
                                                 RaceClass.id,
                                                 Race.id)\
                                       .order_by(Race.date.desc())\
                                       .all()

    return render_template('team_details.html', team=team,\
                           current_racers = current_racers,\
                           results=results)
   

@main.route('/team/add/', methods=['GET', 'POST'])
def team_add():
    if not current_user.is_authenticated:
        abort(403)
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
    if not current_user.is_authenticated:
        abort(403)
    team = Team.query.get_or_404(id)
    form=TeamEditForm(team)
    
    if form.validate_on_submit():
        name = form.name.data
        team.name = name
        db.session.commit()
        flash('Team ' + team.name + ' updated!')
        return redirect(url_for('main.team_details',id=team.id))
        
    form.name.data = team.name
    return render_template('edit.html', item=team,form=form,type='team')

@main.route('/team/delete/<int:id>/')
def team_delete(id):
    if not current_user.is_authenticated:
        abort(403)
    team = Team.query.get_or_404(id)
    db.session.delete(team)
    db.session.commit()
    flash('Team ' + team.name + ' deleted!')
    return redirect(url_for('main.team'))

@main.route('/team/<int:id>/racer/add/', methods=['GET', 'POST'])
def team_add_racer(id):
    if not current_user.is_authenticated:
        abort(403)
    team = Team.query.get_or_404(id)
    form=RacerAddToTeamForm()
    form.name.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                         'autocomplete':'off',
                         'data-source':json.dumps([racer.name for racer in
                                                   Racer.query.all()])}

    if form.validate_on_submit():
        name = form.name.data
        racer_id = Racer.query.filter_by(name=name).first().id
        Racer.query.get(racer_id).current_team_id=team.id
        db.session.commit()
        return redirect(url_for('main.team_details',id=team.id))

    return render_template('add.html', form=form,type='racer to team')
    

@main.route('/race/', methods=['GET', 'POST'])
def race():
    if request.query_string:
        

        if 'start' in request.args:
            start = request.args.get('start')
        else:
            start = None
        if 'end' in request.args:
            end = request.args.get('end')
        else:
            end = None
        if start is not None and end is not None:
            races = Race.query.filter(Race.date.between(start,end)).all()
            races_json = []
            for race in races:
        
                races_json.append({"title":race.race_class.name,\
                                   "start":race.date.strftime('%Y-%m-%d'),\
                                   "url":url_for('main.race_details',
                                                 id=race.id),
                                   "color":race.race_class.color})
            
            return json.dumps(races_json)
    if request.method == 'POST':
        if session['race_view'] == 'calendar':
            session['race_view'] = 'table'
            return redirect(url_for('main.race'))
        else:
            session['race_view']= 'calendar'
            return redirect(url_for('main.race'))
             
    races = Race.query.order_by(desc(Race.date)).all()
    #if session['race_view'] is None:
    if 'race_view' not in session:
        session['race_view']= 'calendar'
    return render_template('race.html', races=races)

@main.route('/race/search/', methods=['GET', 'POST'])
def race_search():
    form=RaceSearchForm()
    form.date.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                         'autocomplete':'off',
                         'data-source':json.dumps([race.date
                                                       .strftime('%m/%d/%Y')
                                                   for race in
                                                   Race.query
                                                   .distinct(Race.date)
                                                   .order_by(Race.date)
                                                   .all()])}

    if form.validate_on_submit():
        date = form.date .data      
        races = Race.query.filter_by(date=date).all()
        if len(races) == 1:
            race=races[0]
            return redirect(url_for('main.race_details',id=race.id))
        else:
            return render_template('race_search.html',races=races,\
                                   form=form)
            
            

    return render_template('race_search.html', races=None,form=form)

@main.route('/race/<int:id>/')
def race_details(id):
    race = Race.query.get_or_404(id)
    points_race = False
    dnf_list=[]
    #I had to do this sort because jinja doesn't support lambas
    participants = sorted(race.participants,
                          key=lambda x: (x.place is None, x.place))

        

    #Let's see if we can figure out if anyone got points in this race
    #We also want to see if they DNFed and put them in a separate list
    for participant in participants:
        if participant.points:
            points_race = True
        if participant.dnf:
            dnf_list.append(participant)


	#for some reason I couldn't remove dnf riders from the previous
    #loop, I couldn't figure out why so I needed to split this up
    for dnf_rider in dnf_list:
        participants.remove(dnf_rider)

    #Generate list of MAR winners
    mar_list = Participant.query.join(Race).filter(Race.id==id)\
                                          .group_by(Participant.id)\
                                          .having(Participant.mar_place>0)\
                                          .order_by(Participant.mar_place)\
                                          .all()
    primes = Prime.query.join(Participant).join(Race).filter(Race.id==id).all()
    return render_template('race_details.html', race=race,
                           participants=participants,
                           points_race=points_race,
                           mar_list=mar_list,
                           dnf_list=dnf_list,
                           primes=primes)


@main.route('/race/add/', methods=['GET', 'POST'])
def race_add():
    if not current_user.is_authenticated:
        abort(403)
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
    if not current_user.is_authenticated:
        abort(403)
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
        starters = form.starters.data

        race.date=date
        race.fast_lap=fast_lap
        race.average_lap=average_lap
        race.slow_lap=slow_lap
        race.weather = weather
        race.class_id=class_id
        race.usac_permit=usac_permit
        race.laps=laps
        race.starters=starters
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' updated!')
        return redirect(url_for('main.race_details',id=race.id))
        
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
    form.starters.data=race.starters
    return render_template('edit.html', item=race,form=form,type='race')

@main.route('/race/delete/<int:id>/')
def race_delete(id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(id)
    db.session.delete(race)
    db.session.commit()
    flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' deleted!')
    return redirect(url_for('main.race'))

@main.route('/race/<int:id>/participant/add/', methods=['GET', 'POST'])
def race_add_participant(id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(id)
    form=ParticipantAddForm(race)
    form.name.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                         'autocomplete':'off',
                         'data-source':json.dumps([racer.name for racer in
                                                   Racer.query.all()])}
    form.team_name.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                              'autocomplete':'off',
                              'data-source':json.dumps([team.name for team in
                                                   Team.query.all()])}
    if form.validate_on_submit():
        race_id = race.id
        racer_id=Racer.query.filter_by(name=form.name.data).first().id
        if form.team_name.data:
            team_id=Team.query.filter_by(name=form.team_name.data).first().id
        else:
            team_id=None

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
        
    #Let's get the next place and pre-populate the form
    if Participant.query.filter(and_(Participant.race_id==id,
                                     Participant.place>0)).count():
        next_place = Participant.query.filter(and_(Participant.race_id==id,
                                                   Participant.place>0))\
                                      .order_by(Participant.place.desc())\
                                      .first()\
                                      .place

    else:
        next_place=0
    form.place.data = next_place + 1

    return render_template('add.html',form=form,type='participant')

    
@main.route('/race/<int:race_id>/participant/edit/<int:participant_id>', methods=['GET', 'POST'])
def race_edit_participant(race_id,participant_id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(race_id)
    participant = Participant.query.get_or_404(participant_id)
    if participant.race_id != race_id:
        abort(404) 
    form=ParticipantEditForm(race)
    form.name.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                         'autocomplete':'off',
                         'data-source':json.dumps([racer.name for racer in
                                                   Racer.query.all()])}
    form.team_name.render_kw={'data-provide': 'typeahead', 'data-items':'4',
                              'autocomplete':'off',
                              'data-source':json.dumps([team.name for team in
                                                   Team.query.all()])}
    if form.validate_on_submit():
        race_id = race.id
        racer_id=Racer.query.filter_by(name=form.name.data).first().id
        if form.team_name.data:
            team_id=Team.query.filter_by(name=form.team_name.data).first().id
        else:
            team_id=None

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
    if participant.team:
        form.team_name.data = participant.team.name
        
    return render_template('edit.html', item=participant,form=form,
                           type='participant')

    
@main.route('/race/<int:race_id>/participant/delete/<int:participant_id>')
def race_delete_participant(race_id,participant_id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(race_id)
    participant = Participant.query.get_or_404(participant_id)
    if participant.race_id != race_id:
        abort(404) 
    db.session.delete(participant)
    flash('Racer ' + participant.racer.name + ' deleted from race!')
    return redirect(url_for('main.race_details',id=race.id))
    
@main.route('/race/<int:id>/prime/add/', methods=['GET', 'POST'])
def race_add_prime(id):
    if not current_user.is_authenticated:
        abort(403)
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
    if not current_user.is_authenticated:
        abort(403)
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
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(race_id)
    prime = Prime.query.get_or_404(prime_id)
    if prime.participant.race.id != race_id:
        abort(404) 
    db.session.delete(prime)
    flash('Prime for ' + prime.participant.racer.name + ' deleted from race!')
    return redirect(url_for('main.race_details',id=race.id))

@main.route('/marshal/')
@login_required
def marshal():
    marshals = Marshal.query.order_by(Marshal.name).all()
    return render_template('marshal.html', marshals = marshals)

@main.route('/marshal/<int:id>/')
@login_required
def marshal_details(id):
    marshal = Marshal.query.get_or_404(id)

    return render_template('marshal_details.html', marshal=marshal)

@main.route('/marshal/add/', methods=['GET', 'POST'])
@login_required
def marshal_add():
    if not current_user.is_authenticated:
        abort(403)
    form=MarshalAddForm()
    if form.validate_on_submit():
        name = form.name.data
        marshal=Marshal(name=name)
        db.session.add(marshal)
        db.session.commit()
        flash('Marshal ' + marshal.name + ' created!')
        return redirect(url_for('main.marshal'))


    return render_template('add.html',form=form,type='marshal')

@main.route('/marshal/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def marshal_edit(id):
    if not current_user.is_authenticated:
        abort(403)
    marshal = Marshal.query.get_or_404(id)
    form=MarshalEditForm(marshal)
    
    if form.validate_on_submit():
        name = form.name.data
        marshal.name = name
        db.session.commit()
        flash('Marshal ' + marshal.name + ' updated!')
        return redirect(url_for('main.marshal'))
        
    form.name.data = marshal.name
    return render_template('edit.html',
                           item=marshal,form=form,type='marshal')

@main.route('/marshal/delete/<int:id>/')
@login_required
def marshal_delete(id):
    if not current_user.is_authenticated:
        abort(403)
    marshal = Marshal.query.get_or_404(id)
    db.session.delete(marshal)
    db.session.commit()
    flash('Marshal ' + marshal.name + ' deleted!')
    return redirect(url_for('main.marshal'))

@main.route('/race/<int:id>/marshal/add/', methods=['GET', 'POST'])
def race_add_marshal(id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(id)
    form=RaceMarshalAddForm()
    form.marshal_id.choices = [(marshal.id, 
                                   marshal.name)
                                   for marshal in 
                                   Marshal.query.all()]
    if form.validate_on_submit():
        marshal_id = form.marshal_id.data
        race_id = race.id
        race_marshal=RaceMarshal(marshal_id = marshal_id, race_id=race_id)
        db.session.add(race_marshal)
        db.session.commit()
        flash('Marshal ' + race_marshal.marshal.name + ' added to race!')
        return redirect(url_for('main.race_details',id=race.id))
    return render_template('add.html',form=form,type='race marshal')

@main.route('/race/<int:race_id>/marshal/delete/<int:race_marshal_id>')
def race_delete_marshal(race_id,race_marshal_id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(race_id)
    race_marshal = RaceMarshal.query.get_or_404(race_marshal_id)
    if race_marshal.race.id != race_id:
        abort(404) 
    db.session.delete(race_marshal)
    flash('Marshal ' + race_marshal.marshal.name + ' deleted from race!')
    return redirect(url_for('main.race_details',id=race.id))

@main.route('/official/')
@login_required
def official():
    officials = Official.query.order_by(Official.name).all()
    return render_template('official.html', officials = officials)

@main.route('/official/<int:id>/')
@login_required
def official_details(id):
    official = Official.query.get_or_404(id)
    return render_template('official_details.html', official=official)

@main.route('/official/add/', methods=['GET', 'POST'])
@login_required
def official_add():
    if not current_user.is_authenticated:
        abort(403)
    form=OfficialAddForm()
    if form.validate_on_submit():
        name = form.name.data
        official=Official(name=name)
        db.session.add(official)
        db.session.commit()
        flash('Official ' + official.name + ' created!!')
        return redirect(url_for('main.official'))


    return render_template('add.html',form=form,type='official')

@main.route('/official/edit/<int:id>/', methods=['GET', 'POST'])
@login_required
def official_edit(id):
    if not current_user.is_authenticated:
        abort(403)
    official = Official.query.get_or_404(id)
    form=OfficialEditForm(official)
    
    if form.validate_on_submit():
        name = form.name.data
        official.name = name
        db.session.commit()
        flash('Official ' + official.name + ' updated!')
        return redirect(url_for('main.official'))
        
    form.name.data = official.name
    return render_template('edit.html',
                           item=official,form=form,type='official')

@main.route('/official/delete/<int:id>/')
@login_required
def official_delete(id):
    if not current_user.is_authenticated:
        abort(403)
    official = Official.query.get_or_404(id)
    db.session.delete(official)
    db.session.commit()
    flash('Official ' + official.name + ' deleted!')
    return redirect(url_for('main.official'))

@main.route('/race/<int:id>/official/add/', methods=['GET', 'POST'])
def race_add_official(id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(id)
    form=RaceOfficialAddForm()
    form.official_id.choices = [(official.id, 
                                   official.name)
                                   for official in 
                                   Official.query.all()]
    if form.validate_on_submit():
        official_id= form.official_id.data
        race_id = race.id
        race_official=RaceOfficial(official_id = official_id, race_id=race_id)
        db.session.add(race_official)
        db.session.commit()
        flash('Official ' + race_official.official.name + ' added to race!')
        return redirect(url_for('main.race_details',id=race.id))
    return render_template('add.html',form=form,type='race official')

@main.route('/race/<int:race_id>/official/delete/<int:race_official_id>')
def race_delete_official(race_id,race_official_id):
    if not current_user.is_authenticated:
        abort(403)
    race = Race.query.get_or_404(race_id)
    race_official = RaceOfficial.query.get_or_404(race_official_id)
    if race_official.race.id != race_id:
        abort(404) 
    db.session.delete(race_official)
    flash('Official ' + race_official.official.name + ' deleted from race!')
    return redirect(url_for('main.race_details',id=race.id))


@main.route('/standings/', methods=['GET', 'POST'])
def standings():
    form = StandingsSearchForm()
    form.year.choices = sorted(set([(int(year.date.strftime('%Y')),
                                     int(year.date.strftime('%Y')))
                                  for year in Race.query.all()]),reverse=True)
    
    form.race_class_id.choices = [(race_class_id.id, race_class_id.name)
                                  for race_class_id in
                                  RaceClass.query.order_by('name')]
    if form.validate_on_submit():
        year = form.year.data
        race_class_id = form.race_class_id.data
        standings_type = form.standings_type.data
	results = generate_standings(year,race_class_id,standings_type)
        return render_template('standings.html', form=form, results=results, 
                                                 standings_type=standings_type)
    return render_template('standings.html', form=form, results=None)

@main.route('/feedback/', methods=['GET', 'POST'])
def send_feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        name = form.name.data
        replyaddress = form.replyaddress.data
        subject = form.subject.data
        feedback = form.feedback.data
        send_feedback_email(name,replyaddress, subject, feedback)
        #This is clunky, but I'm going to also add the feedback to a gdoc
        url = 'https://docs.google.com/forms/u/0/d/1zIzQcf-T-R15LBZXTekcOXtD-DuBthlTBX_W4KZXId8/formResponse'
        form_data = { 'entry.1964141134': name,
                      'entry.768109921':replyaddress,
                      'entry.994423798':subject,
                      'entry.282921535': feedback,
                      'draftResponse':[],
                      'pageHistory':0}
        user_agent = {'Referer':'https://docs.google.com/forms/d/1zIzQcf-T-R15LBZXTekcOXtD-DuBthlTBX_W4KZXId8/viewform','User-Agent': "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.52 Safari/537.36"}
        
        resp = requests.post(url,data=form_data,headers=user_agent)
        flash('Feedback sent!')
        return redirect(url_for('main.index'))
    return render_template('feedback.html', form=form)

@main.route('/robots.txt')
def serve_static():
   return current_app.send_static_file('robots.txt')

