import json
from flask import render_template, redirect, url_for, flash, current_app
from .. import db
from ..models import Racer, Team, Race, Participant
from . import racer
from .forms import RacerAddForm, RacerEditForm, RacerSearchForm
from flask_login import current_user
from ..decorators import roles_accepted

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
    return render_template('racer/details.html', racer=racer,
                           current_team=current_team, teams=teams)

@racer.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official')
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
        strava_id = form.strava_id.data
        birthdate = form.birthdate.data
        if form.current_team.data:
            current_team_id = Team.query.filter_by(name=form.current_team.data)\
                                      .first().id
        else:
            current_team_id = None
        racer = Racer(name=name, usac_license=usac_license, birthdate=birthdate,
                      current_team_id=current_team_id,
                      strava_id=strava_id)
        db.session.add(racer)
        db.session.commit()
        flash('Racer ' + racer.name + ' created!')
        current_app.logger.info('%s[%d]', racer.name, racer.id)
        return redirect(url_for('racer.index'))


    return render_template('add.html', form=form, type='racer')

@racer.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official')
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
        strava_id = form.strava_id.data
        racer.strava_id = strava_id
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
    form.strava_id.data = racer.strava_id
    if racer.current_team_id:
        form.current_team.data = Team.query.get(racer.current_team_id).name
    return render_template('edit.html',
                           item=racer, form=form, type='racer')

@racer.route('/delete/<int:id>/')
@roles_accepted('official')
def delete(id):
    racer = Racer.query.get_or_404(id)
    current_app.logger.info('%s[%d]', racer.name, racer.id)
    db.session.delete(racer)
    db.session.commit()
    flash('Racer ' + racer.name + ' deleted!')
    return redirect(url_for('racer.index'))
