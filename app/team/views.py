import json
from flask import render_template, redirect, url_for, flash, current_app
from sqlalchemy import func
from .. import db
from ..models import RaceClass, Racer, Team, Race, Participant
from .forms import TeamAddForm, TeamEditForm, RacerAddToTeamForm
from flask_login import current_user
from . import team
from ..decorators import roles_accepted

@team.route('/')
def index():
    teams = Team.query.order_by(Team.name).all()
    return render_template('team/index.html', teams=teams)


@team.route('/<int:id>/')
def details(id):
    team = Team.query.get_or_404(id)
    current_racers = team.current_racers
    results = Race.query.with_entities(Race.date,
                                       RaceClass.name,
                                       func.count(Racer.id),
                                       Race.id)\
                                       .join(Participant)\
                                       .join(Racer)\
                                       .join(Team,
                                             Team.id == Participant.team_id)\
                                       .join(RaceClass)\
                                       .filter(Team.id == team.id)\
                                       .group_by(Race.date,
                                                 RaceClass.id,
                                                 Race.id)\
                                       .order_by(Race.date.desc())\
                                       .order_by(RaceClass.name)\
                                       .all()

    return render_template('team/details.html', team=team,\
                           current_racers=current_racers,\
                           results=results)

@team.route('/add/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def add():
    form = TeamAddForm()
    if form.validate_on_submit():
        name = form.name.data
        team = Team(name=name)
        db.session.add(team)
        db.session.commit()
        flash('Team ' + team.name + ' created!')
        current_app.logger.info('%s[%d]', team.name, team.id)
        return redirect(url_for('team.index'))


    return render_template('add.html', form=form, type='team')

@team.route('/edit/<int:id>/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def edit(id):
    team = Team.query.get_or_404(id)
    form = TeamEditForm(team)
    if form.validate_on_submit():
        name = form.name.data
        team.name = name
        db.session.commit()
        flash('Team ' + team.name + ' updated!')
        current_app.logger.info('%s[%d]', team.name, team.id)
        return redirect(url_for('team.details', id=team.id))
    form.name.data = team.name
    return render_template('edit.html', item=team, form=form, type='team')

@team.route('/delete/<int:id>/')
@roles_accepted('official', 'moderator')
def delete(id):
    team = Team.query.get_or_404(id)
    current_app.logger.info('%s[%d]', team.name, team.id)
    db.session.delete(team)
    db.session.commit()
    flash('Team ' + team.name + ' deleted!')
    return redirect(url_for('team.index'))

@team.route('/<int:id>/racer/add/', methods=['GET', 'POST'])
@roles_accepted('official', 'moderator')
def add_racer(id):
    team = Team.query.get_or_404(id)
    form = RacerAddToTeamForm()
    form.name.render_kw = {'data-provide': 'typeahead', 'data-items':'4',
                           'autocomplete':'off',
                           'data-source':json.dumps([racer.name for racer in
                                                     Racer.query.all()])}

    if form.validate_on_submit():
        name = form.name.data
        racer_id = Racer.query.filter_by(name=name).first().id
        Racer.query.get(racer_id).current_team_id = team.id
        db.session.commit()
        flash('Added ' + name + ' to ' + team.name)
        current_app.logger.info('%s[%d]:%s[%d]', team.name, team.id, name,
                                racer_id)
        return redirect(url_for('team.details', id=team.id))

    return render_template('add.html', form=form, type='racer to team')
