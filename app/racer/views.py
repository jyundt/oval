import datetime
import json

from flask import render_template, redirect, url_for, flash, current_app,\
                  request
from sqlalchemy import extract
from stravalib import Client

from . import racer as racer_
from .forms import *
from .. import db
from ..decorators import roles_accepted
from ..models import AcaMembership, RaceClass, Racer, Team, Race, Participant


@racer_.route('/')
def index():
    seasons = set(
        int(date.year) for (date,) in Race.query.with_entities(Race.date).all())
    race_classes = {
        race_class.id: race_class for race_class in
        RaceClass.query}

    recent_date = datetime.date.today() - datetime.timedelta(days=365)
    recent_seasons = set(int(val[0]) for val in
                         Race.query.with_entities(extract('year', Race.date))
                         .filter(Race.date >= recent_date)
                         .group_by(extract('year', Race.date)))
    season_range_default = [min(recent_seasons), max(recent_seasons)]

    return render_template(
        'racer/index.html',
        seasons=sorted(seasons, reverse=True),
        race_classes=race_classes,
        season_range_default=season_range_default)


@racer_.route('/filter')
def filter_():
    def extract_int_list(s):
        for val in (s or '').split(','):
            try:
                yield int(val)
            except ValueError: pass

    filter_seasons = sorted(extract_int_list(request.args.get('filter_seasons')))[:2]
    if not filter_seasons or len(filter_seasons) != 2:
        filter_seasons = None

    race_classes = {
        race_class.id: race_class for race_class in
        RaceClass.query}

    filter_race_class_ids = set(
        race_class_id for race_class_id in extract_int_list(request.args.get('filter_race_class_ids'))
        if race_class_id in race_classes.keys())

    query = Racer.query.join(Participant, isouter=True).join(Race, isouter=True)
    if filter_seasons:
        query = (query.filter(extract('year', Race.date) >= filter_seasons[0])
                      .filter(extract('year', Race.date) <= filter_seasons[1]))
    else:
        query = (query.filter(Race.date.is_(None)))
    if filter_race_class_ids:
        query = query.filter(Race.class_id.in_(filter_race_class_ids))
    racers = query.order_by(Racer.name).all()

    racer_info = [{
        'id': racer.id,
        'name': racer.name,
        'strava_id': racer.strava_id,
        'current_team_id': racer.current_team_id,
        'current_team_name': racer.current_team.name if racer.current_team else ''}
                  for racer in racers]
    return json.dumps(racer_info)

@racer_.route('/search/', methods=['GET', 'POST'])
def search():
    form = RacerSearchForm()
    form.name.render_kw = {'data-provide': 'typeahead',
                           'data-items': '4',
                           'autocomplete': 'off',
                           'data-source': json.dumps([racer.name for racer in
                                                     Racer.query.all()])}

    if form.validate_on_submit():
        name = form.name.data
        racers = Racer.query.filter(Racer.name.ilike('%'+name+'%')).all()
        if len(racers) == 1:
            racer = racers[0]
            return redirect(url_for('racer.details', id=racer.id))
        else:
            return render_template('racer/search.html', racers=racers,
                                   form=form)
    return render_template('racer/search.html', racers=None, form=form)


@racer_.route('/head2head/', methods=['GET', 'POST'])
def head2head():
    # Request parameters:
    # name1, name2: names to use explicitly to populate the form values
    # racer1, racer2: specific racer ids, overrides names if valid

    racers = {racer.id: racer for racer in Racer.query.all()}

    form = RacerHead2HeadForm()
    name_fields = [form.name1, form.name2]
    for field in [form.name1, form.name2]:
        field.render_kw = {
            'data-provide': 'typeahead',
            'data-items': '4',
            'autocomplete': 'off',
            'data-source': json.dumps(
                [racer.name for racer in racers.values()])}

    # Process name parameters first, populating form
    for i in xrange(2):
        reqname = request.args.get('name%d' % (i+1))
        if reqname:
            name_fields[i].data = reqname

    # Process racer id parameters (overwriting form name values if valid)
    racer_ids = [None, None]
    for i in xrange(2):
        racer_id = request.args.get('racer%d' % (i+1))
        if racer_id:
            racer_id = int(racer_id) if racer_id.isdigit() else None
        if racer_id in racers:
            racer_ids[i] = racer_id
            name_fields[i].data = racers[racer_id].name

    # Empty form; nothing to do
    if not any(field.data for field in name_fields):
        return render_template('racer/head2head_search.html', form=form)

    def get_matching_racers_by_name(name):
        return [racer for racer in racers.values() if name.lower() in racer.name.lower()][:10]

    # For racers without an id, search by name.
    matching_racers = [
        (i, [racers[racer_ids[i]]] if racer_ids[i] else get_matching_racers_by_name(name_fields[i].data))
        for i in xrange(2)]

    # If we have multiple possible matches for either field, present list of
    # #search matches for selection,
    if any(len(matches[1]) != 1 for matches in matching_racers):
        return render_template(
            'racer/head2head_search.html',
            matching_racers=matching_racers, form=form,
            racer1=racer_ids[0], racer2=racer_ids[1])

    # We have an unambiguous set of matches.  Do the head-to-head comparison.
    racers = [matches[0] for _, matches in matching_racers]

    # Redirect to GET for final comaprison
    if request.method == 'POST':
        return redirect(url_for('racer.head2head', racer1=racers[0].id, racer2=racers[1].id))

    racer_subqueries = [
        (Participant.query
            .with_entities(Participant.race_id, Participant.place)
            .join(Racer, Participant.racer_id == Racer.id)
            .filter(Racer.id == racer.id).subquery('racer%d' % (i+1)))
        for i, racer in enumerate(racers)]

    results_query = (db.session.query(racer_subqueries[0])
        .with_entities(
            racer_subqueries[0].c.place.label('racer1_place'),
            racer_subqueries[1].c.place.label('racer2_place'),
            Race.date,
            Race.id.label('race_id'))
        .join(
            racer_subqueries[1],
            racer_subqueries[0].c.race_id == racer_subqueries[1].c.race_id)
        .join(Race, Race.id == racer_subqueries[0].c.race_id)
        .order_by(Race.date))

    class Result(object):
        def __init__(self, sa_result):
            self.racer1_place = sa_result.racer1_place
            self.racer2_place = sa_result.racer2_place
            self.race_id = sa_result.race_id
            self.race_date = sa_result.date

        @staticmethod
        def result_comp(place1, place2):
            if place1 == place2:
                return False
            if not place2:
                return True
            return place1 < place2

        @property
        def racer1_better(self):
            return self.result_comp(self.racer1_place, self.racer2_place)

        @property
        def racer2_better(self):
            return self.result_comp(self.racer2_place, self.racer1_place)

    results = [Result(result) for result in results_query]

    return render_template(
        'racer/head2head.html', racer1=racers[0], racer2=racers[1], results=results,
        racer1_better_count=sum(1 for result in results if result.racer1_better),
        racer2_better_count=sum(1 for result in results if result.racer2_better))


@racer_.route('/<int:id>/')
def details(id):
    racer = Racer.query.get_or_404(id)
    teams = (Team.query.join(Participant)
             .join(Racer)
             .filter_by(id=id)
             .join(Race)
             .order_by(Race.date.desc())
             .all())
    current_team = racer.current_team
    if current_team in teams:
        teams.remove(current_team)

    current_year = datetime.date.today().year
    current_membership = (
        AcaMembership.query.with_entities(
            AcaMembership.paid,
            RaceClass.name.label('season_pass'))
        .join(RaceClass, RaceClass.id == AcaMembership.season_pass, isouter=True)
        .filter(AcaMembership.year == current_year)
        .filter(AcaMembership.racer_id == racer.id)
    ).first()

    strava_client = Client()
    strava_client_id = current_app.config['STRAVA_CLIENT_ID']
    strava_url = (
        strava_client.authorization_url(
            client_id=strava_client_id,
            redirect_uri=url_for('racer.authorize_strava', _external=True),
            state=racer.id,
            approval_prompt='force'))

    if racer.strava_access_token:
        access_token = racer.strava_access_token
        try:
            strava_client = Client(access_token)
            strava_client.get_athlete()
        except Exception:
            racer.strava_access_token = None
            racer.strava_id = None
            racer.strava_email = None
            racer.strava_profile_url = None
            racer.strava_profile_last_fetch = None
            current_app.logger.info('forced strava deauth %s[%d]', racer.name, racer.id)
            db.session.commit()

    return render_template('racer/details.html', racer=racer,
                           current_membership=current_membership,
                           current_team=current_team, teams=teams,
                           strava_url=strava_url)


def get_membership_choices():
    race_classes = RaceClass.query
    return (
        [('none', 'Not a member'), ('member', 'ACA member')] +
        [(str(race_class.id), 'Season Pass: %s' % race_class.name) for race_class in race_classes])


def handle_racer_form(form, current_year, racer=None, current_membership=None):
    name = form.name.data
    usac_license = form.usac_license.data
    birthdate = form.birthdate.data
    current_team_id = (
        Team.query.filter_by(name=form.current_team.data).first().id
        if form.current_team.data else None)
    is_member = form.aca_membership.data == 'member' or form.aca_membership.data.isdigit()
    season_pass = int(form.aca_membership.data) if form.aca_membership.data.isdigit() else None
    paid = form.paid.data

    if racer:
        racer.name = name
        racer.usac_license = usac_license
        racer.birthdate = birthdate
        racer.current_team_id = current_team_id
    else:
        racer = Racer(name=name, usac_license=usac_license, birthdate=birthdate,
                      current_team_id=current_team_id)
        db.session.add(racer)
        db.session.flush()
        db.session.refresh(racer)

    if is_member:
        if current_membership:
            current_membership.is_member = is_member
            current_membership.season_pass = season_pass
            current_membership.paid = paid
        else:
            aca_membership = AcaMembership(
                year=current_year, racer_id=racer.id,
                season_pass=season_pass, paid=paid)
            db.session.add(aca_membership)
    else:
        if current_membership:
            db.session.delete(current_membership)

    db.session.commit()
    flash('Racer ' + racer.name + ' updated!')
    current_app.logger.info('%s[%d]', racer.name, racer.id)
    return redirect(url_for('racer.details', id=racer.id))


@racer_.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def add():
    form = RacerAddForm()
    form.current_team.render_kw = {
        'data-provide': 'typeahead',
        'data-items': '4',
        'autocomplete': 'off',
        'data-source': json.dumps(
           [team.name for team in Team.query.all()])}
    form.aca_membership.choices = get_membership_choices()

    if form.validate_on_submit():
        current_year = datetime.date.today().year
        return handle_racer_form(form, current_year)

    return render_template('add.html', form=form, type='racer')


@racer_.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def edit(id):
    racer = Racer.query.get_or_404(id)
    form = RacerEditForm(racer)
    form.current_team.render_kw = {
        'data-provide': 'typeahead',
        'data-items': '4',
        'autocomplete': 'off',
        'data-source': json.dumps(
            [team.name for team in Team.query.all()])}
    form.aca_membership.choices = get_membership_choices()

    try:
        current_year = int(request.args.get('current_year'))
    except (ValueError, TypeError):
        current_year = datetime.date.today().year
    current_membership = (
        AcaMembership.query
        .filter(AcaMembership.year == current_year)
        .filter(AcaMembership.racer_id == racer.id)
    ).first()

    if form.validate_on_submit():
        return handle_racer_form(form, current_year, racer, current_membership)

    form.name.data = racer.name
    form.usac_license.data = racer.usac_license
    form.birthdate.data = racer.birthdate
    if racer.current_team_id:
        form.current_team.data = Team.query.get(racer.current_team_id).name
    if current_membership:
        form.aca_membership.data = (
            str(current_membership.season_pass)
            if current_membership.season_pass is not None
            else 'member')
        form.paid.data = current_membership.paid

    return render_template('edit.html',
                           item=racer, form=form, type='racer')


@racer_.route('/delete/<int:id>/')
@roles_accepted('official', 'moderator')
def delete(id):
    racer = Racer.query.get_or_404(id)
    current_app.logger.info('%s[%d]', racer.name, racer.id)
    db.session.delete(racer)
    db.session.commit()
    flash('Racer ' + racer.name + ' deleted!')
    return redirect(url_for('racer.index'))


@racer_.route('/membership')
@roles_accepted('official')
def membership_list():
    years = sorted(
        (member.year for member in AcaMembership.query.distinct(AcaMembership.year)),
        reverse=True)
    try:
        req_year = int(request.args.get('year'))
    except (ValueError, TypeError):
        req_year = None
    current_year = datetime.date.today().year
    year = req_year or (years[0] if years else current_year)

    members = (
        AcaMembership.query.with_entities(
            AcaMembership.racer_id, Racer.name,
            RaceClass.name.label('season_pass_class'),
            AcaMembership.paid)
        .join(Racer, AcaMembership.racer_id == Racer.id)
        .join(RaceClass, AcaMembership.season_pass == RaceClass.id, isouter=True)
        .filter(AcaMembership.year == year)
        .order_by(Racer.name)).all()

    return render_template('racer/membership.html', selected_year=year, years=years, members=members)


@racer_.route('/authorize/strava/')
def authorize_strava():
    if request.args.get('state') and request.args.get('code'):
        id = request.args.get('state')
        strava_code = request.args.get('code')
        strava_client_id = current_app.config['STRAVA_CLIENT_ID']
        strava_client_secret = current_app.config['STRAVA_CLIENT_SECRET']
        strava_client = Client()
        try:
            access_token = (
                strava_client.exchange_code_for_token(
                    client_id=strava_client_id,
                    client_secret=strava_client_secret,
                    code=strava_code))
        except Exception:
            return redirect(url_for('racer.index'))
        else:
            racer = Racer.query.get_or_404(id)
            strava_client = Client(access_token)
            strava_athlete = strava_client.get_athlete()
            existing_racer = Racer.query\
                                  .filter_by(strava_id=strava_athlete.id)\
                                  .first()
            if existing_racer:
                flash('Racer ' + existing_racer.name +
                      ' already linked with Strava account for ' +
                      strava_athlete.firstname + ' ' +
                      strava_athlete.lastname + '!')
                current_app.logger.info('%s[%d] failed against %s[%d]',
                                        racer.name, racer.id,
                                        existing_racer.name, existing_racer.id)
                return redirect(url_for('racer.details', id=id))
            else:
                racer.strava_access_token = access_token
                racer.strava_id = strava_athlete.id
                racer.strava_email = strava_athlete.email
                racer.profile_url = strava_athlete.profile
                db.session.commit()
                current_app.logger.info('%s[%d]', racer.name, racer.id)
                flash('Racer ' + racer.name + ' linked with Strava!')
            return redirect(url_for('racer.details', id=id))

    return redirect(url_for('racer.index'))


@racer_.route('/deauthorize/strava/<int:id>/')
@roles_accepted('official', 'moderator')
def deauthorize_strava(id):
    racer = Racer.query.get_or_404(id)
    if racer.strava_access_token:
        strava_access_token = racer.strava_access_token
        strava_client = Client(strava_access_token)
        strava_client.deauthorize()
        racer.strava_access_token = None
        racer.strava_id = None
        racer.strava_email = None
        racer.strava_profile_url = None
        racer.strava_profile_last_fetch = None
        current_app.logger.info('%s[%d]', racer.name, racer.id)
        db.session.commit()
        flash('Racer ' + racer.name + ' deauthorized from Strava!')
    return redirect(url_for('racer.details', id=id))
