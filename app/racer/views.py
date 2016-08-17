import json
import requests
from flask import render_template, redirect, url_for, flash, current_app,\
                  request
from .. import db
from ..models import Racer, Team, Race, Participant
from . import racer
from .forms import RacerAddForm, RacerEditForm, RacerSearchForm
from flask_login import current_user
from ..decorators import roles_accepted
from stravalib import Client

@racer.route('/')
def index():
    racers = Racer.query.order_by(Racer.name).all()
    return render_template('racer/index.html', racers=racers)

@racer.route('/search/', methods=['GET', 'POST'])
def search():
    form = RacerSearchForm()
    form.name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                           'autocomplete':'off',
                           'data-source':json.dumps([racer.name for racer in
                                                     Racer.query.all()])}

    if form.validate_on_submit():
        name = form.name.data
        racers = Racer.query.filter(Racer.name.ilike('%'+name+'%')).all()
        if len(racers) == 1:
            racer = racers[0]
            return redirect(url_for('racer.details', id=racer.id))
        else:
            return render_template('racer/search.html', racers=racers,\
                                   form=form)
    return render_template('racer/search.html', racers=None, form=form)

@racer.route('/<int:id>/')
def details(id):
    racer = Racer.query.get_or_404(id)
    teams = Team.query.join(Participant)\
                      .join(Racer)\
                      .filter_by(id=id)\
                      .join(Race)\
                      .order_by(Race.date.desc())\
                      .all()
    current_team = racer.current_team
    if current_team in teams:
        teams.remove(current_team)

    strava_client = Client()
    strava_client_id = current_app.config['STRAVA_CLIENT_ID']
    strava_url = strava_client.\
                 authorization_url(client_id=strava_client_id,\
                                   redirect_uri=\
                                     url_for('racer.authorize_strava',\
                                             _external=True),\
                                   state=racer.id,\
                                   approval_prompt='force')

    if racer.strava_access_token:
        access_token = racer.strava_access_token
        try:
            strava_client = Client(access_token)
            strava_athlete = strava_client.get_athlete()
        except:
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

@racer.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def add():
    form = RacerAddForm()
    form.current_team.render_kw = {'data-provide': 'typeahead',
                                   'data-items':'4',
                                   'autocomplete':'off',
                                   'data-source':json.dumps([team.name for team\
                                                             in
                                                             Team.query
                                                             .all()])}
    if form.validate_on_submit():
        name = form.name.data
        usac_license = form.usac_license.data
        birthdate = form.birthdate.data
        aca_member = form.aca_member.data
        if form.current_team.data:
            current_team_id = Team.query.filter_by(name=form.current_team.data)\
                                      .first().id
        else:
            current_team_id = None
        racer = Racer(name=name, usac_license=usac_license, birthdate=birthdate,
                      current_team_id=current_team_id, aca_member=aca_member)
        db.session.add(racer)
        db.session.commit()
        flash('Racer ' + racer.name + ' created!')
        current_app.logger.info('%s[%d]', racer.name, racer.id)
        return redirect(url_for('racer.index'))


    return render_template('add.html', form=form, type='racer')

@racer.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def edit(id):
    racer = Racer.query.get_or_404(id)
    form = RacerEditForm(racer)
    form.current_team.render_kw = {'data-provide': 'typeahead',
                                   'data-items':'4',
                                   'autocomplete':'off',
                                   'data-source':json.dumps([team.name for team\
                                                             in
                                                             Team.query
                                                             .all()])}
    if form.validate_on_submit():
        name = form.name.data
        racer.name = name
        usac_license = form.usac_license.data
        racer.usac_license = usac_license
        birthdate = form.birthdate.data
        racer.birthdate = birthdate
        aca_member = form.aca_member.data
        racer.aca_member = aca_member
        if form.current_team.data:
            current_team_id = Team.query\
                                  .filter_by(name=form.current_team.data)\
                                  .first().id
        else:
            current_team_id = None
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

@racer.route('/delete/<int:id>/')
@roles_accepted('official', 'moderator')
def delete(id):
    racer = Racer.query.get_or_404(id)
    current_app.logger.info('%s[%d]', racer.name, racer.id)
    db.session.delete(racer)
    db.session.commit()
    flash('Racer ' + racer.name + ' deleted!')
    return redirect(url_for('racer.index'))

@racer.route('/authorize/strava/')
def authorize_strava():
    if request.args.get('state') and request.args.get('code'):
        racer_id=request.args.get('state')     
        strava_code=request.args.get('code')     

        strava_client_id = current_app.config['STRAVA_CLIENT_ID']
        strava_client_secret= current_app.config['STRAVA_CLIENT_SECRET']
      
        strava_client = Client()
        try:
            access_token = strava_client.\
                             exchange_code_for_token(client_id=strava_client_id,
                                                     client_secret=\
                                                       strava_client_secret,\
                                                     code=strava_code)

        except:
            return redirect(url_for('racer.index'))
        else:
            racer = Racer.query.get_or_404(racer_id) 
            strava_client = Client(access_token)
            strava_athlete = strava_client.get_athlete()
            existing_racer = Racer.query\
                                  .filter_by(strava_id=strava_athlete.id)\
                                  .first()
            if existing_racer:
                flash('Racer ' + existing_racer.name +\
                      ' already linked with Strava account for '+\
                        strava_athlete.firstname + ' ' +\
                        strava_athlete.lastname + '!')
                current_app.logger.info('%s[%d] failed against %s[%d]',\
                                        racer.name, racer.id,\
                                        existing_racer.name, existing_racer.id)
                return redirect(url_for('racer.details', id=racer_id))
            else:
                racer.strava_access_token = access_token
                racer.strava_id = strava_athlete.id
                racer.strava_email = strava_athlete.email
                racer.profile_url = strava_athlete.profile
                db.session.commit()
                current_app.logger.info('%s[%d]',racer.name, racer.id)
                flash('Racer ' + racer.name + ' linked with Strava!') 
            return redirect(url_for('racer.details', id=racer_id))

    return redirect(url_for('racer.index'))

@racer.route('/deauthorize/strava/<int:id>/')
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
    return redirect(url_for('racer.details',id=id))
