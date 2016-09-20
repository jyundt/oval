import json
import datetime

from flask import render_template, redirect, url_for, flash, current_app,\
                  request
from sqlalchemy import extract
from stravalib import Client

from . import racer as racer_
from .forms import RacerAddForm, RacerEditForm, RacerSearchForm
from .. import db
from ..decorators import roles_accepted
from ..models import RaceClass, Racer, Team, Race, Participant


@racer_.route('/')
def index():
    def extract_int_list(s):
        for val in (s or '').split(','):
            try:
                yield int(val)
            except ValueError: pass

    seasons = set(
        int(date.year) for (date,) in Race.query.with_entities(Race.date).all())
    race_classes = {
        race_class.id: race_class for race_class in
        RaceClass.query}

    if request.args.get('filter_seasons') is None and request.args.get('filter_seasons') is None:
        recent_date = datetime.date.today() - datetime.timedelta(days=365)
        filter_seasons = set(int(val[0]) for val in
            Race.query.with_entities(extract('year', Race.date))
            .filter(Race.date >= recent_date)
            .group_by(extract('year', Race.date)))
    else:
        filter_seasons = set(
            season for season in extract_int_list(request.args.get('filter_seasons'))
            if season in seasons)
    filter_race_class_ids = set(
        race_class_id for race_class_id in extract_int_list(request.args.get('filter_race_class_ids'))
        if race_class_id in race_classes.keys())

    query = Racer.query.join(Participant).join(Race)
    if filter_seasons:
        query = query.filter(extract('year', Race.date).in_(filter_seasons))
    if filter_race_class_ids:
        query = query.filter(Race.class_id.in_(filter_race_class_ids))
    racers = query.order_by(Racer.name).all()
    return render_template(
        'racer/index.html', racers=racers,
        seasons=sorted(seasons, reverse=True),
        race_classes=race_classes,
        filter_seasons=sorted(filter_seasons),
        filter_race_class_ids=[
            race_class.id for race_class in sorted(race_classes.values(), key=lambda rc: rc.name)
            if race_class.id in filter_race_class_ids])


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
                           current_team=current_team, teams=teams,
                           strava_url=strava_url)


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

    if form.validate_on_submit():
        name = form.name.data
        usac_license = form.usac_license.data
        birthdate = form.birthdate.data
        aca_member = form.aca_member.data
        current_team_id = (
            Team.query.filter_by(name=form.current_team.data).first().id
            if form.current_team.data else None)
        racer = Racer(name=name, usac_license=usac_license, birthdate=birthdate,
                      current_team_id=current_team_id, aca_member=aca_member)
        db.session.add(racer)
        db.session.commit()
        flash('Racer ' + racer.name + ' created!')
        current_app.logger.info('%s[%d]', racer.name, racer.id)
        return redirect(url_for('racer.index'))

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

    if form.validate_on_submit():
        name = form.name.data
        racer.name = name
        usac_license = form.usac_license.data
        racer.usac_license = usac_license
        birthdate = form.birthdate.data
        racer.birthdate = birthdate
        aca_member = form.aca_member.data
        racer.aca_member = aca_member
        current_team_id = (
            Team.query.filter_by(name=form.current_team.data).first().id
            if form.current_team.data else None)
        racer.current_team_id = current_team_id
        db.session.commit()
        flash('Racer ' + racer.name + ' updated!')
        current_app.logger.info('%s[%d]', racer.name, racer.id)
        return redirect(url_for('racer.details', id=racer.id))

    form.name.data = racer.name
    form.usac_license.data = racer.usac_license
    form.birthdate.data = racer.birthdate
    form.aca_member.data = racer.aca_member
    if racer.current_team_id:
        form.current_team.data = Team.query.get(racer.current_team_id).name
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
