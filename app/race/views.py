import json
from flask import render_template, session, redirect, url_for, flash, abort,\
                  request
from sqlalchemy import and_
from .. import db
from ..models import Official, Marshal, RaceClass, Racer, Team, Race,\
                     Participant, RaceOfficial, RaceMarshal, Prime
from . import race
from .forms import RaceEditForm, RaceAddForm, ParticipantAddForm,\
                   ParticipantEditForm, PrimeAddForm,\
                   PrimeEditForm, RaceMarshalAddForm, RaceOfficialAddForm,\
                   RaceSearchForm
from datetime import timedelta, datetime
from ..decorators import roles_accepted

@race.route('/', methods=['GET', 'POST'])
def index():
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
            races = Race.query.filter(Race.date.between(start, end)).all()
            races_json = []
            for race in races:
                races_json.append({"title":race.race_class.name,\
                                   "start":race.date.strftime('%Y-%m-%d'),\
                                   "url":url_for('race.details',
                                                 id=race.id),
                                   "color":race.race_class.color})
            return json.dumps(races_json)
    if request.method == 'POST':
        if session['race_view'] == 'calendar':
            session['race_view'] = 'table'
            return redirect(url_for('race.index'))
        else:
            session['race_view'] = 'calendar'
            return redirect(url_for('race.index'))
    races = Race.query.order_by(Race.date.desc()).all()
    if 'race_view' not in session:
        session['race_view'] = 'calendar'
    return render_template('race/index.html', races=races)

@race.route('/search/', methods=['GET', 'POST'])
def search():
    form = RaceSearchForm()
    form.date.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                           'autocomplete':'off',
                           'data-source':json.dumps([race.date
                                                     .strftime('%m/%d/%Y')
                                                     for race in
                                                     Race.query
                                                     .distinct(Race.date)
                                                     .order_by(Race.date)
                                                     .all()])}

    if form.validate_on_submit():
        date = form.date.data
        races = Race.query.filter_by(date=date).all()
        if len(races) == 1:
            race = races[0]
            return redirect(url_for('race.details', id=race.id))
        else:
            return render_template('race/search.html', races=races,\
                                   form=form)
    return render_template('race/search.html', races=None, form=form)

@race.route('/<int:id>/')
def details(id):
    race = Race.query.get_or_404(id)
    points_race = False
    dnf_list = []
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
    mar_list = Participant.query.join(Race).filter(Race.id == id)\
                                          .group_by(Participant.id)\
                                          .having(Participant.mar_place > 0)\
                                          .order_by(Participant.mar_place)\
                                          .all()
    primes = Prime.query.join(Participant).join(Race).filter(Race.id == id).all()
    return render_template('race/details.html', race=race,
                           participants=participants,
                           points_race=points_race,
                           mar_list=mar_list,
                           dnf_list=dnf_list,
                           primes=primes)


@race.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add():
    form = RaceAddForm()
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

        race = Race(date=date, fast_lap=fast_lap, average_lap=average_lap,
                    slow_lap=slow_lap, weather=weather, class_id=class_id,
                    usac_permit=usac_permit, laps=laps)
        db.session.add(race)
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' created!')
        return redirect(url_for('race.index'))


    form.submit.label.text = 'Add'
    form.date.data = datetime.today()
    return render_template('add.html', form=form, type='race')

@race.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
def edit(id):
    race = Race.query.get_or_404(id)
    form = RaceEditForm(race)
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
        race.date = date
        race.fast_lap = fast_lap
        race.average_lap = average_lap
        race.slow_lap = slow_lap
        race.weather = weather
        race.class_id = class_id
        race.usac_permit = usac_permit
        race.laps = laps
        race.starters = starters
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' updated!')
        return redirect(url_for('race.details', id=race.id))
    form.date.data = race.date
    form.class_id.data = race.class_id
    #This is so clunky :(
    if race.fast_lap is not None:
        form.fast_lap.data = datetime.strptime(str(race.fast_lap), '%H:%M:%S')
    if race.average_lap is not None:
        form.average_lap.data = datetime.strptime(str(race.average_lap),
                                                  '%H:%M:%S')
    if race.slow_lap is not None:
        form.slow_lap.data = datetime.strptime(str(race.slow_lap), '%H:%M:%S')
    form.weather.data = race.weather
    form.usac_permit.data = race.usac_permit
    form.laps.data = race.laps
    form.starters.data = race.starters
    return render_template('edit.html', item=race, form=form, type='race')

@race.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    race = Race.query.get_or_404(id)
    db.session.delete(race)
    db.session.commit()
    flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' deleted!')
    return redirect(url_for('race.index'))

@race.route('/<int:id>/participant/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add_participant(id):
    race = Race.query.get_or_404(id)
    form = ParticipantAddForm(race)
    form.name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                           'autocomplete':'off',
                           'data-source':json.dumps([racer.name for racer in
                                                     Racer.query.all()])}
    form.team_name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                                'autocomplete':'off',
                                'data-source':json.dumps([team.name for team in
                                                          Team.query.all()])}
    if form.validate_on_submit():
        race_id = race.id
        racer_id = Racer.query.filter_by(name=form.name.data).first().id
        if form.team_name.data:
            team_id = Team.query.filter_by(name=form.team_name.data).first().id
        else:
            team_id = None

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
        participant = Participant(racer_id=racer_id, team_id=team_id,
                                  points=points, team_points=team_points,
                                  mar_place=mar_place, mar_points=mar_points,
                                  point_prime=point_prime, dnf=dnf, dns=dns,
                                  relegated=relegated,
                                  disqualified=disqualified,
                                  race_id=race_id, place=place)
        db.session.add(participant)
        db.session.commit()
        return redirect(url_for('race.details', id=race.id))
    #Let's get the next place and pre-populate the form
    if Participant.query.filter(and_(Participant.race_id == id,
                                     Participant.place > 0)).count():
        next_place = Participant.query.filter(and_(Participant.race_id == id,
                                                   Participant.place > 0))\
                                      .order_by(Participant.place.desc())\
                                      .first()\
                                      .place

    else:
        next_place = 0
    form.place.data = next_place + 1

    return render_template('add.html', form=form, type='participant')

@race.route('/<int:race_id>/participant/edit/<int:participant_id>',
            methods=['GET', 'POST'])
@roles_accepted('official')
def edit_participant(race_id, participant_id):
    race = Race.query.get_or_404(race_id)
    participant = Participant.query.get_or_404(participant_id)
    if participant.race_id != race_id:
        abort(404)
    form = ParticipantEditForm(race)
    form.name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                           'autocomplete':'off',
                           'data-source':json.dumps([racer.name for racer in
                                                     Racer.query.all()])}
    form.team_name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                                'autocomplete':'off',
                                'data-source':json.dumps([team.name for team in
                                                          Team.query.all()])}
    if form.validate_on_submit():
        race_id = race.id
        racer_id = Racer.query.filter_by(name=form.name.data).first().id
        if form.team_name.data:
            team_id = Team.query.filter_by(name=form.team_name.data).first().id
        else:
            team_id = None

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
        participant.racer_id = racer_id
        participant.team_id = team_id
        participant.place = place
        participant.points = points
        participant.team_points = team_points
        participant.mar_place = mar_place
        participant.mar_points = mar_points
        participant.point_prime = point_prime
        participant.dnf = dnf
        participant.dns = dns
        participant.relegated = relegated
        participant.disqualified = disqualified
        db.session.commit()
        return redirect(url_for('race.details', id=race.id))

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
    return render_template('edit.html', item=participant, form=form,
                           type='participant')

@race.route('/<int:race_id>/participant/delete/<int:participant_id>')
@roles_accepted('official')
def delete_participant(race_id, participant_id):
    race = Race.query.get_or_404(race_id)
    participant = Participant.query.get_or_404(participant_id)
    if participant.race_id != race_id:
        abort(404)
    db.session.delete(participant)
    flash('Racer ' + participant.racer.name + ' deleted from race!')
    return redirect(url_for('race.details', id=race.id))

@race.route('/<int:id>/prime/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add_prime(id):
    race = Race.query.get_or_404(id)
    form = PrimeAddForm()
    form.participant_id.choices = [(participant_id.id,
                                    participant_id.racer.name)
                                   for participant_id in
                                   Race.query.get(id).participants]
    if form.validate_on_submit():
        participant_id = form.participant_id.data
        name = form.name.data
        prime = Prime(name=name, participant_id=participant_id)
        db.session.add(prime)
        db.session.commit()
        flash('Prime for ' + prime.participant.racer.name + ' added!')
        return redirect(url_for('race.details', id=race.id))
    return render_template('add.html', form=form, type='prime')

@race.route('/<int:race_id>/prime/edit/<int:prime_id>/', methods=['GET',
                                                                  'POST'])
@roles_accepted('official')
def edit_prime(race_id, prime_id):
    race = Race.query.get_or_404(race_id)
    prime = Prime.query.get_or_404(prime_id)
    if prime.participant.race.id != race_id:
        abort(404)
    form = PrimeEditForm()
    if form.validate_on_submit():
        name = form.name.data
        prime.name = name
        db.session.commit()
        flash('Prime for ' + prime.participant.racer.name + ' updated!')
        return redirect(url_for('race.details', id=race.id))

    form.name.data = prime.name
    return render_template('edit.html', item=prime, form=form, type='prime')

@race.route('/<int:race_id>/prime/delete/<int:prime_id>')
@roles_accepted('official')
def delete_prime(race_id, prime_id):
    race = Race.query.get_or_404(race_id)
    prime = Prime.query.get_or_404(prime_id)
    if prime.participant.race.id != race_id:
        abort(404)
    db.session.delete(prime)
    flash('Prime for ' + prime.participant.racer.name + ' deleted from race!')
    return redirect(url_for('race.details', id=race.id))

@race.route('/<int:id>/marshal/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add_marshal(id):
    race = Race.query.get_or_404(id)
    form = RaceMarshalAddForm()
    form.marshal_id.choices = [(marshal.id,
                                marshal.name)
                               for marshal in
                               Marshal.query.all()]
    if form.validate_on_submit():
        marshal_id = form.marshal_id.data
        race_id = race.id
        race_marshal = RaceMarshal(marshal_id=marshal_id, race_id=race_id)
        db.session.add(race_marshal)
        db.session.commit()
        flash('Marshal ' + race_marshal.marshal.name + ' added to race!')
        return redirect(url_for('race.details', id=race.id))
    return render_template('add.html', form=form, type='race marshal')

@race.route('/<int:race_id>/marshal/delete/<int:race_marshal_id>')
@roles_accepted('official')
def delete_marshal(race_id, race_marshal_id):
    race = Race.query.get_or_404(race_id)
    race_marshal = RaceMarshal.query.get_or_404(race_marshal_id)
    if race_marshal.race.id != race_id:
        abort(404)
    db.session.delete(race_marshal)
    flash('Marshal ' + race_marshal.marshal.name + ' deleted from race!')
    return redirect(url_for('race.details', id=race.id))

@race.route('/<int:id>/official/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add_official(id):
    race = Race.query.get_or_404(id)
    form = RaceOfficialAddForm()
    form.official_id.choices = [(official.id,
                                 official.name)
                                for official in
                                Official.query.all()]
    if form.validate_on_submit():
        official_id = form.official_id.data
        race_id = race.id
        race_official = RaceOfficial(official_id=official_id, race_id=race_id)
        db.session.add(race_official)
        db.session.commit()
        flash('Official ' + race_official.official.name + ' added to race!')
        return redirect(url_for('race.details', id=race.id))
    return render_template('add.html', form=form, type='race official')

@race.route('/<int:race_id>/official/delete/<int:race_official_id>')
@roles_accepted('official')
def delete_official(race_id, race_official_id):
    race = Race.query.get_or_404(race_id)
    race_official = RaceOfficial.query.get_or_404(race_official_id)
    if race_official.race.id != race_id:
        abort(404)
    db.session.delete(race_official)
    flash('Official ' + race_official.official.name + ' deleted from race!')
    return redirect(url_for('race.details', id=race.id))
