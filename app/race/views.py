import json
import boto3
import hashlib
from flask import render_template, session, redirect, url_for, flash, abort,\
                  request, current_app, make_response
from sqlalchemy import and_
from sqlalchemy import extract

from .. import db
from ..models import Official, Marshal, RaceClass, Racer, Team, Race,\
                     Participant, RaceOfficial, RaceMarshal, Prime, Course,\
                     NotificationEmail, AcaMembership, RaceAttachment
from . import race
from .forms import RaceEditForm, RaceAddForm, ParticipantAddForm,\
                   ParticipantEditForm, PrimeAddForm,\
                   PrimeEditForm, RaceMarshalAddForm, RaceOfficialAddForm,\
                   RaceSearchForm, AttachmentAddForm, AttachmentEditForm
from datetime import timedelta, datetime
from ..decorators import roles_accepted
from ..email import send_email
from werkzeug.utils import secure_filename

@race.route('/')
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

    if request.args.get('race_view') in ['calendar', 'table']:
        session['race_view'] = request.args['race_view']
    if 'race_view' not in session:
        session['race_view'] = 'calendar'

    races_query = (
        Race.query
        .join(RaceClass)
        .join(Course))

    years = sorted(set(
        int(date.year) for (date,) in Race.query.with_entities(Race.date).all()),
        reverse=True)
    if session['race_view'] == 'table':
        try:
            req_year = int(request.args.get('year'))
        except (ValueError, TypeError):
            req_year = None
        year = req_year if req_year is not None else (years[0] if years else None)
        races_query = races_query.filter(extract("year", Race.date) == year)
    else:
        year = None

    races_query = races_query.order_by(Race.date.desc(), RaceClass.name)
    races = races_query.all()

    return render_template('race/index.html', races=races, years=years, selected_year=year)


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
    dnf_list = []
    #I had to do this sort because jinja doesn't support lambas
    participants = sorted(race.participants,
                          key=lambda x: (x.place is None, x.place))

    #Let's see if we can figure out if anyone got points in this race
    #We also want to see if they DNFed and put them in a separate list
    for participant in participants:
        if participant.dnf:
            dnf_list.append(participant)


	#for some reason I couldn't remove dnf riders from the previous
    #loop, I couldn't figure out why so I needed to split this up
    for dnf_rider in dnf_list:
        if dnf_rider.point_prime:
            #If a DNF rider won the point prime, put them at the end
            participants.remove(dnf_rider)
            participants.append(dnf_rider)
        else:
            participants.remove(dnf_rider)

    #Generate list of MAR winners
    mar_list = Participant.query.join(Race).filter(Race.id == id)\
                                          .group_by(Participant.id)\
                                          .having(Participant.mar_place > 0)\
                                          .order_by(Participant.mar_place)\
                                          .all()
    primes = Prime.query.join(Participant)\
                        .join(Race)\
                        .filter(Race.id == id).all()

    attachments = RaceAttachment.query.join(Race)\
                                      .filter(Race.id == id)\
                                      .order_by(RaceAttachment.id)\
                                      .all()
    return render_template('race/details.html', race=race,
                           participants=participants,
                           mar_list=mar_list,
                           dnf_list=dnf_list,
                           primes=primes,
                           attachments=attachments)


@race.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add():
    form = RaceAddForm()
    form.class_id.choices = [(class_id.id, class_id.name) for class_id in
                             RaceClass.query.order_by('name')]
    form.course_id.choices = [(course_id.id, course_id.name) for course_id in
                              Course.query.order_by('name')]
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
        if form.winning_time.data is not None:
            winning_time = timedelta(0, form.winning_time.data.minute * 60
                                     + form.winning_time.data.second
                                     + form.winning_time.data.hour * 3600)
        else:
            winning_time = form.winning_time.data
        weather = form.weather.data
        class_id = form.class_id.data
        course_id = form.course_id.data
        usac_permit = form.usac_permit.data
        laps = form.laps.data
        starters = form.starters.data
        points_race = form.points_race.data
        picnic_race = form.picnic_race.data
        notes = form.notes.data

        race = Race(date=date, fast_lap=fast_lap, average_lap=average_lap,
                    slow_lap=slow_lap, weather=weather, class_id=class_id,
                    usac_permit=usac_permit, laps=laps, course_id=course_id,
                    winning_time=winning_time, points_race=points_race,
                    starters=starters, notes=notes, picnic_race=picnic_race)
        db.session.add(race)
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' created!')
        current_app.logger.info('%s[%d]', race.name, race.id)
        if 'submit' in request.form:
            return redirect(url_for('race.details', id=race.id))
        elif 'submit_another' in request.form:
            return redirect(url_for('race.add'))
        else:
            abort(404)

    form.date.data = datetime.today()
    #Let's also prepopulate the points_race field if we are in June/July/Aug
    if (form.date.data.month >= 6) and (form.date.data.month <= 8):
        form.points_race.data = True
    default_course = Course.query.filter(Course.is_default == True).first()
    if default_course:
        form.course_id.data = default_course.id
    return render_template('add.html', form=form, type='race')

@race.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
def edit(id):
    race = Race.query.get_or_404(id)
    form = RaceEditForm(race)
    form.class_id.choices = [(class_id.id, class_id.name) for class_id in
                             RaceClass.query.order_by('name')]
    form.course_id.choices = [(course_id.id, course_id.name) for course_id in
                              Course.query.order_by('name')]
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
        if form.winning_time.data is not None:
            winning_time = timedelta(0, form.winning_time.data.minute * 60
                                     + form.winning_time.data.second
                                     + form.winning_time.data.hour * 3600)
        else:
            winning_time = form.winning_time.data
        weather = form.weather.data
        class_id = form.class_id.data
        course_id = form.course_id.data
        usac_permit = form.usac_permit.data
        laps = form.laps.data
        starters = form.starters.data
        notes = form.notes.data
        points_race = form.points_race.data
        picnic_race = form.picnic_race.data
        race.date = date
        race.fast_lap = fast_lap
        race.average_lap = average_lap
        race.slow_lap = slow_lap
        race.winning_time = winning_time
        race.weather = weather
        race.class_id = class_id
        race.course_id = course_id
        race.usac_permit = usac_permit
        race.laps = laps
        race.starters = starters
        race.notes = notes
        race.points_race = points_race
        race.picnic_race = picnic_race
        db.session.commit()
        flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' updated!')
        current_app.logger.info('%s[%d]', race.name, race.id)
        return redirect(url_for('race.details', id=race.id))
    form.date.data = race.date
    form.class_id.data = race.class_id
    form.course_id.data = race.course_id
    #This is so clunky :(
    if race.fast_lap is not None:
        form.fast_lap.data = datetime.strptime(str(race.fast_lap), '%H:%M:%S')
    if race.average_lap is not None:
        form.average_lap.data = datetime.strptime(str(race.average_lap),
                                                  '%H:%M:%S')
    if race.slow_lap is not None:
        form.slow_lap.data = datetime.strptime(str(race.slow_lap), '%H:%M:%S')
    if race.winning_time is not None:
        form.winning_time.data = datetime.strptime(str(race.winning_time),
                                                   '%H:%M:%S')
    form.weather.data = race.weather
    form.usac_permit.data = race.usac_permit
    form.laps.data = race.laps
    form.starters.data = race.starters
    form.notes.data = race.notes
    form.points_race.data = race.points_race
    form.picnic_race.data = race.picnic_race
    return render_template('edit.html', item=race, form=form, type='race')

@race.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    race = Race.query.get_or_404(id)
    current_app.logger.info('%s[%d]', race.name, race.id)
    db.session.delete(race)
    db.session.commit()
    flash('Race for ' + race.date.strftime('%m/%d/%Y') + ' deleted!')
    return redirect(url_for('race.index'))

@race.route('/<int:id>/participant/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add_participant(id):
    race = Race.query.get_or_404(id)
    form = ParticipantAddForm(race)
    year = datetime.now().year
    form.name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                           'autocomplete':'off',
                           'data-source':json.dumps([racer.name for racer in
                                                     Racer.query.all()])}
    form.team_name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                                'autocomplete':'off',
                                'data-source':json.dumps([team.name for team in
                                                          Team.query.all()])}
    form.team_name.description = '(Leave blank to assign current team.)'
    if form.validate_on_submit():
        race_id = race.id
        racer_id = Racer.query.filter_by(name=form.name.data).first().id
        if form.team_name.data:
            team_id = Team.query.filter_by(name=form.team_name.data)\
                                .first().id
        else:
            if (Race.query.get(race_id).date.year == year) and\
            Racer.query.get(racer_id).current_team:
                team_id = Racer.query.get(racer_id).current_team.id
            else:
                team_id = None

        place = form.place.data
        mar_place = form.mar_place.data
        point_prime = form.point_prime.data
        dnf = form.dnf.data
        dns = form.dns.data
        relegated = form.relegated.data
        disqualified = form.disqualified.data
        #Let's check to see if we are in a points race
        if Race.query.get(race_id).points_race and\
           Race.query.get(race_id).date.year == year:
            mar_point_dict = {1: 3, 2: 2, 3: 1}
            membership_info = (
                AcaMembership.query.with_entities(AcaMembership.paid.label('paid'))
                .join(Racer)
                .filter(Racer.id == racer_id)
                .filter(AcaMembership.year == year).one_or_none())
            membership_paid = membership_info and membership_info.paid
            if membership_paid:
                points = form.points.data
                #Check to see if we manually specified mar points
                #if not, guess at them
                if point_prime:
                    #If points is "blank", set it to zero
                    if points is None:
                        points = 0
                    points += 1
                if mar_place:
                    mar_points = mar_point_dict[mar_place]
                else:
                    mar_points = None
                if team_id:
                #Verify that 3 members of the team didn't already get points
                    if Participant.query\
                                  .filter(Participant.race_id == race_id)\
                                  .filter(Participant.team_id == team_id)\
                                  .filter(Participant.team_points > 0)\
                                  .count() >= 3:
                        team_points = None
                        flash(Team.query.get(team_id).name + ' already scored\
                              points for three places, removing team points.')
                    else:
                        team_points = form.team_points.data
                else:
                    team_points = None
                    flash(Racer.query.get(racer_id).name + ' is not on a team,\
                          removing team points.')
            else:
                flash(Racer.query.get(racer_id).name + ' is not a current \
                      ACA member, removing points.')
                points = None
                mar_points = None
                team_points = None
        else:
            points = form.points.data
            mar_points = form.mar_points.data
            team_points = form.team_points.data
        #Because we are pre-populating Place, let's set it to None for DNF
        if dnf:
            place = None
        participant = Participant(racer_id=racer_id, team_id=team_id,
                                  points=points, team_points=team_points,
                                  mar_place=mar_place, mar_points=mar_points,
                                  point_prime=point_prime, dnf=dnf, dns=dns,
                                  relegated=relegated,
                                  disqualified=disqualified,
                                  race_id=race_id, place=place)
        db.session.add(participant)
        db.session.commit()
        flash('Racer ' + participant.racer.name + ' added to race!')
        current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                                participant.racer.name, participant.id)
        #Let's also add a Prime of "Point Prime" if necessary
        if point_prime:
            participant_id = participant.id
            name = "Point Prime"
            prime = Prime(name=name, participant_id=participant_id)
            db.session.add(prime)
            db.session.commit()
            flash('Prime for ' + prime.participant.racer.name + ' added!')
            current_app.logger.info('%s[%d]:%s[%d]:%s[%d]', race.name, race.id,
                                    participant.racer.name, participant.id,
                                    prime.name, prime.id)
 
        if 'submit' in request.form:
            return redirect(url_for('race.details', id=race.id))
        elif 'submit_another' in request.form:
            return redirect(url_for('race.add_participant', id=race.id))
        else:
            abort(404)
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

    if race.points_race:
        point_dict = {1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2,\
                      8: 1}
        #Let's define a dict for place -> point mapping
        if form.place.data in point_dict:
            form.points.data = point_dict[form.place.data]
            form.team_points.data = point_dict[form.place.data]
        else:
            form.points.data = None
            form.team_points.data = None
    else:
        #I guess we don't need the points fields
        del form.points
        del form.team_points
        del form.mar_points
        del form.point_prime
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
        flash('Racer ' + participant.racer.name + ' updated in race!')
        current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                                participant.racer.name, participant.id)
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
    current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                            participant.racer.name, participant.id)
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
        participant = Participant.query.get(participant_id)
        prime = Prime(name=name, participant_id=participant_id)
        db.session.add(prime)
        db.session.commit()
        flash('Prime for ' + prime.participant.racer.name + ' added!')
        current_app.logger.info('%s[%d]:%s[%d]:%s[%d]', race.name, race.id,
                                participant.racer.name, participant.id,
                                prime.name, prime.id)
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
        participant_id = prime.participant_id
        participant = Participant.query.get(participant_id)
        prime.name = name
        db.session.commit()
        flash('Prime for ' + prime.participant.racer.name + ' updated!')
        current_app.logger.info('%s[%d]:%s[%d]:%s[%d]', race.name, race.id,
                                participant.racer.name, participant.id,
                                prime.name, prime.id)
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
    participant_id = prime.participant_id
    participant = Participant.query.get(participant_id)
    current_app.logger.info('%s[%d]:%s[%d]:%s[%d]', race.name, race.id,
                            participant.racer.name, participant.id,
                            prime.name, prime.id)
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
        current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                                race_marshal.marshal.name,
                                race_marshal.id)
        return redirect(url_for('race.details', id=race.id))
    return render_template('add.html', form=form, type='race marshal')

@race.route('/<int:race_id>/marshal/delete/<int:race_marshal_id>')
@roles_accepted('official')
def delete_marshal(race_id, race_marshal_id):
    race = Race.query.get_or_404(race_id)
    race_marshal = RaceMarshal.query.get_or_404(race_marshal_id)
    if race_marshal.race.id != race_id:
        abort(404)
    current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                            race_marshal.marshal.name, race_marshal.id)
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
        current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                                race_official.official.name,
                                race_official.id)
        return redirect(url_for('race.details', id=race.id))
    return render_template('add.html', form=form, type='race official')

@race.route('/<int:race_id>/official/delete/<int:race_official_id>')
@roles_accepted('official')
def delete_official(race_id, race_official_id):
    race = Race.query.get_or_404(race_id)
    race_official = RaceOfficial.query.get_or_404(race_official_id)
    if race_official.race.id != race_id:
        abort(404)
    current_app.logger.info('%s[%d]:%s[%d]', race.name, race.id,
                            race_official.official.name,
                            race_official.id)
    db.session.delete(race_official)
    flash('Official ' + race_official.official.name + ' deleted from race!')
    return redirect(url_for('race.details', id=race.id))

@race.route('/<int:id>/email/')
@roles_accepted('official')
def email(id):
    race = Race.query.get_or_404(id)
    participants = sorted(race.participants,
                          key=lambda x: (x.place is None, x.place))
    notificationemails = NotificationEmail.query.all()
    recipients = [r.email for r in notificationemails]
    for recipient in recipients:
        send_email(recipient,
                   race.date.strftime('%m/%d/%Y') + ' ' + race.race_class.name\
                   + ' Race Results Posted',
                   'email/new_results',
                   race=race, participants=participants[:3])
    current_app.logger.info('%s[%d]', race.name, race.id)
    flash('Results for race on ' + race.date.strftime('%m/%d/%Y') + ' emailed!')
    return redirect(url_for('race.details', id=id))

@race.route('/<int:id>/download_text/')
def download_text(id):
    race = Race.query.get_or_404(id)
    dnf_list = []
    #I had to do this sort because jinja doesn't support lambas
    participants = sorted(race.participants,
                          key=lambda x: (x.place is None, x.place))

    #Let's see if we can figure out if anyone got points in this race
    #We also want to see if they DNFed and put them in a separate list
    for participant in participants:
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
    primes = Prime.query.join(Participant)\
                        .join(Race)\
                        .filter(Race.id == id).all()
    textfile = render_template('race/details.txt', race=race,
                               participants=participants,
                               mar_list=mar_list,
                               dnf_list=dnf_list,
                               primes=primes)
    response = make_response(textfile)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=cr" +\
                                              race.date.strftime('%m%d%y') +\
                                              '_' + race.race_class.name +\
                                              '.txt'
    return response

@race.route('/<int:id>/attachment/add/', methods=['GET', 'POST'])
@roles_accepted('official')
def add_attachment(id):
    race = Race.query.get_or_404(id)
    form = AttachmentAddForm()

    if form.validate_on_submit():
        description = form.description.data
        attachment = form.attachment.data
        attachment_name = secure_filename(attachment.filename)
        attachment_mimetype = attachment.mimetype
        if not (attachment_mimetype == "image/jpeg" or \
           attachment_mimetype == "application/pdf"):
            flash ('Unsupported attachment type!')
            return redirect(url_for('race.add_attachment', id=race.id))

   
        attachment_hash = hashlib.md5(attachment.stream.read())
        attachment_md5 = attachment_hash.hexdigest()
        previous_attachment = RaceAttachment.query\
                                            .filter_by(key=attachment_md5)\
                                            .first()
        
        if previous_attachment:
            previous_race = Race.query.get(previous_attachment.race_id)
            flash ('Cannot attach file, already associated with ' +
                   previous_race.name + ' race!')
            return redirect(url_for('race.add_attachment', id=race.id))
            
        
        #Let's get back to the start of the file, otherwise we are at EOF
        attachment.stream.seek(0)
        s3_secret_key = current_app.config['S3_SECRET_KEY']
        s3_access_key = current_app.config['S3_ACCESS_KEY']
        s3_bucket_name = current_app.config['S3_BUCKET']

        #This could probably use some better error handling...but...mneh
        try: 
            s3_resource = boto3.resource('s3', use_ssl=True,
                                         aws_secret_access_key=s3_secret_key,
                                         aws_access_key_id=s3_access_key)
            s3_bucket = s3_resource.Bucket(s3_bucket_name)
            s3_bucket.put_object(Body=attachment.stream,
                                 Key=attachment_md5,
                                 ContentMD5=attachment_hash.digest()
                                                           .encode('base64')
                                                           .strip())

        except Exception as e:
            flash('Failed to upload attachment!')
            current_app.logger.info('%s[%d] %s', race.name, race.id, e)
            return redirect(url_for('race.add_attachment', id=race.id))

        race_attachment = RaceAttachment(key=attachment_md5, race_id=race.id,
                                         description=description,
                                         filename=attachment_name,
                                         mimetype=attachment_mimetype)

        db.session.add(race_attachment)
        db.session.commit()
        flash('Attachment for ' + str(race.name) + ' added!')
        current_app.logger.info('%s[%d]:[%d] %s',race.name,race.id,
                                race_attachment.id, race_attachment.filename)
        return redirect(url_for('race.details', id=race.id))
    return render_template('add.html', form=form, type='attachment')

@race.route('/<int:race_id>/attachment/edit/<int:attachment_id>/',
            methods=['GET', 'POST'])
@roles_accepted('official')
def edit_attachment(race_id, attachment_id):
    race = Race.query.get_or_404(race_id)
    attachment = RaceAttachment.query.get_or_404(attachment_id)
    if attachment.race_id != race_id:
        abort(404)
    form = AttachmentEditForm()
    if form.validate_on_submit():
        description = form.description.data 
        attachment.description = description

        db.session.commit()
        flash('Attachment for ' + str(race.name) + ' updated!')
        current_app.logger.info('%s[%d]:[%d] %s',race.name,race.id,
                                attachment.id, attachment.filename)
        return redirect(url_for('race.details', id=race.id))

    form.description.data = attachment.description
    return render_template('edit.html', item=attachment, form=form, type='attachment')

@race.route('/<int:race_id>/attachment/delete/<int:attachment_id>')
@roles_accepted('official')
def delete_attachment(race_id, attachment_id):
    race = Race.query.get_or_404(race_id)
    attachment = RaceAttachment.query.get_or_404(attachment_id)
    if attachment.race_id != race_id:
        abort(404)

    s3_secret_key = current_app.config['S3_SECRET_KEY']
    s3_access_key = current_app.config['S3_ACCESS_KEY']
    s3_bucket_name = current_app.config['S3_BUCKET']

    try:
        s3_resource = boto3.resource('s3', use_ssl=True,
                                     aws_secret_access_key=s3_secret_key,
                                     aws_access_key_id=s3_access_key)
        s3_resource.Object(s3_bucket_name, attachment.key).delete()
    except Exception as e:
        flash('Failed to delete attachment!')
        current_app.logger.info('%s[%d] %s', race.name, race.id, e)
        return redirect(url_for('race.details', id=race.id))


    current_app.logger.info('%s[%d]:[%d] %s',race.name,race.id,
                            attachment.id, attachment.filename)
    db.session.delete(attachment)
    flash('Attachment for ' + str(race.name) + ' deleted!')
    return redirect(url_for('race.details', id=race.id))


@race.route('/<int:race_id>/attachment/download/<int:attachment_id>')
@roles_accepted('official')
def download_attachment(race_id, attachment_id):
    race = Race.query.get_or_404(race_id)
    attachment = RaceAttachment.query.get_or_404(attachment_id)
    if attachment.race_id != race_id:
        abort(404)

    s3_secret_key = current_app.config['S3_SECRET_KEY']
    s3_access_key = current_app.config['S3_ACCESS_KEY']
    s3_bucket_name = current_app.config['S3_BUCKET']

    try:
        s3_resource = boto3.resource('s3', use_ssl=True,
                                     aws_secret_access_key=s3_secret_key,
                                     aws_access_key_id=s3_access_key)
        file = s3_resource.Object(s3_bucket_name, attachment.key)\
                          .get()['Body']\
                          .read()
                          
    except Exception as e:
        flash('Failed to download attachment!')
        current_app.logger.info('%s[%d] %s', race.name, race.id, e)
        return redirect(url_for('race.details', id=race.id))

    response = make_response(file)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + \
                                              attachment.filename
                                         
    return response

@race.route('/<int:race_id>/attachment/view/<int:attachment_id>')
@roles_accepted('official')
def view_attachment(race_id, attachment_id):
    race = Race.query.get_or_404(race_id)
    attachment = RaceAttachment.query.get_or_404(attachment_id)
    if attachment.race_id != race_id:
        abort(404)

    s3_secret_key = current_app.config['S3_SECRET_KEY']
    s3_access_key = current_app.config['S3_ACCESS_KEY']
    s3_bucket_name = current_app.config['S3_BUCKET']

    try:
        s3_resource = boto3.resource('s3', use_ssl=True,
                                     aws_secret_access_key=s3_secret_key,
                                     aws_access_key_id=s3_access_key)
        file = s3_resource.Object(s3_bucket_name, attachment.key)\
                          .get()['Body']\
                          .read()
                          
    except Exception as e:
        flash('Failed to open attachment!')
        current_app.logger.info('%s[%d] %s', race.name, race.id, e)
        return redirect(url_for('race.details', id=race.id))

    response = make_response(file)
    response.headers['Content-Type'] = attachment.mimetype
    response.headers['Content-Disposition'] = "inline; filename=" + \
                                              attachment.filename
                                         
    return response
