import datetime
import requests
from collections import OrderedDict, defaultdict

from flask import render_template, redirect, url_for, current_app, flash
from sqlalchemy import extract, func, and_
from ..models import RaceClass, Racer, Team, Race, Participant
from ..email import send_feedback_email
from . import main
from .forms import StandingsSearchForm, FeedbackForm


def _gen_default(year, race_class_id, race_calendar):
    """Default error case for standings type parameter

    It seems useful to create a full function here in case any logging,
    or more important work should be done on error.
    """
    return None


def _gen_race_calendar(year, race_class_id):
    """Returns the full calendar of dates for a class and year of racing

    This is necessary because dates where individuals do not participate will
    not exist in their individual results otherwise.
    """
    dates = Race.query.with_entities(Race.date, Race.id)\
                    .filter(extract("year", Race.date) == year)\
                    .filter(Race.points_race == True)\
                    .filter(Race.class_id == race_class_id).all()
    dates = sorted(dates, key=lambda x: x[0])

    return dates


def _make_result(name, id_, total_pts, pts, race_calendar, team_name, team_id):
    """Create result dictionary to make html templates more readable
    """
    result = {"name": name,
              "id": id_,
              "total_pts": total_pts,
              "race_pts": OrderedDict([(date, "-") for date,_ in race_calendar]),
              "team_name": team_name,
              "team_id": team_id}

    for point, date in pts:
        if point:
            result["race_pts"][date] = point

    return result


def _gen_team_standings(year, race_class_id, race_calendar):
    """Return team standings with individual race and total points
    """
    results = []
    teams = Team.query.with_entities(Team.name,
                                       func.sum(Participant.team_points),\
                                       Team.id)\
                        .join(Participant)\
                        .join(Race)\
                        .join(RaceClass)\
                        .group_by(Team.id)\
                        .filter(and_(Race.class_id == race_class_id,\
                                     extract('year', Race.date) == year))\
                        .having(func.sum(Participant.team_points) > 0)\
                        .order_by(func.sum(Participant.team_points)\
                        .desc()).all()
    for team in teams:
        points = Participant.query.with_entities(func.sum(Participant.team_points), Race.date)\
            .join(Race)\
            .group_by(Participant.team_id, Race.date)\
            .filter(team[2] == Participant.team_id)\
            .filter(extract("year", Race.date) == year)\
            .filter(Race.points_race == True)\
            .filter(Race.class_id == race_class_id).all()

        result = _make_result(name=team[0], id_=team[2], total_pts=team[1],
                              pts=points, race_calendar=race_calendar,
                              team_name=None, team_id=None)
        
        results.append(result)

    return results


def _gen_ind_standings(year, race_class_id, race_calendar):
    """Return top individual racer standings with individual race and total points
    """
    results = []
    racers = Racer.query.with_entities(Racer.name, func.sum(Participant.points), Racer.id)\
                         .join(Participant)\
                         .join(Race)\
                         .join(RaceClass)\
                         .group_by(Racer.id)\
                         .filter(and_(and_(Race.class_id == race_class_id, extract('year', Race.date) == year),
                                 Race.points_race == True))\
                         .having(func.sum(Participant.points) > 0)\
                         .order_by(func.sum(Participant.points)\
                         .desc()).all()

    for racer in racers:
        points = Participant.query.with_entities(Participant.points, Race.date)\
            .join(Racer)\
            .join(Race)\
            .filter(and_(racer[2] == Participant.racer_id, Race.points_race == True))\
            .filter(extract("year", Race.date) == year)\
            .filter(Race.class_id == race_class_id).all()

        team = Team.query.with_entities(Team.name, Team.id)\
                         .join(Participant)\
                         .join(Racer)\
                         .filter(Racer.id==racer[2])\
                         .join(Race)\
                         .order_by(Race.date.asc())\
                         .filter(and_(and_(Race.class_id == race_class_id,
                                           extract('year', Race.date) == year),
                                           Race.points_race == True))\
                         .all()

        if team:
            team = team[-1]
        else:
            team.append(None)
            team.append(None)



        result = _make_result(name=racer[0], id_=racer[2], total_pts=racer[1],
                              pts=points, race_calendar=race_calendar,
                              team_name=team[0], team_id=team[1])
        
        results.append(result)

    return results


def _gen_mar_standings(year, race_class_id, race_calendar):
    """Return top MAR standings with individual race and total points
    """
    results = []
    mars = Racer.query.with_entities(Racer.name,
                                        func.sum(Participant.mar_points),\
                                        Racer.id)\
                         .join(Participant)\
                         .join(Race)\
                         .join(RaceClass)\
                         .group_by(Racer.id)\
                         .filter(and_(Race.class_id == race_class_id,\
                                      extract('year', Race.date) == year))\
                         .having(func.sum(Participant.mar_points) > 0)\
                         .order_by(func.sum(Participant.mar_points)\
                         .desc()).all()
    for racer in mars:
        points = Participant.query.with_entities(Participant.mar_points, Race.date)\
            .join(Racer)\
            .join(Race)\
            .filter(and_(racer[2] == Participant.racer_id, Race.points_race == True))\
            .filter(extract("year", Race.date) == year)\
            .filter(Race.class_id == race_class_id).all()

        team = Team.query.with_entities(Team.name, Team.id)\
                         .join(Participant)\
                         .join(Racer)\
                         .filter(Racer.id==racer[2])\
                         .join(Race)\
                         .order_by(Race.date.asc())\
                         .filter(and_(and_(Race.class_id == race_class_id,
                                           extract('year', Race.date) == year),
                                           Race.points_race == True))\
                         .all()

        if team:
            team = team[-1]
        else:
            team.append(None)
            team.append(None)

        result = _make_result(name=racer[0], id_=racer[2], total_pts=racer[1],
                              pts=points, race_calendar=race_calendar,
                              team_name=team[0], team_id=team[1])

        results.append(result)

    return results     


def generate_standings(year, race_class_id, standings_type):
    """Returns a table for the current standings in a specific season.
    
    """
    STANDING_TYPES = defaultdict(_gen_default,
                                team=_gen_team_standings,
                                individual=_gen_ind_standings,
                                mar=_gen_mar_standings)
    
    race_calendar = _gen_race_calendar(year, race_class_id)

    results =  STANDING_TYPES[standings_type](year, race_class_id, race_calendar)

    return results, race_calendar


@main.route('/')
def index():
    """Fills and renders the front page index.html template
    
    Let's hard code the categories that we'd like to see on the front page
    """
    categories = ['A', 'B', 'C', 'Masters 40+/Women']
    races = []
    for category in categories:
        races.append(Race.query.join(RaceClass)\
                               .filter_by(name=category)\
                               .order_by(Race.date.desc())\
                               .first())
    return render_template('index.html', races=races)


@main.route('/standings/', methods=['GET', 'POST'])
def standings():
    form = StandingsSearchForm()
    form.year.choices = sorted(set([(int(year.date.strftime('%Y')),
                                     int(year.date.strftime('%Y')))
                                    for year in Race.query\
                                                    .all()]), reverse=True)

    form.race_class_id.choices = [(race_class_id.id, race_class_id.name)
                                  for race_class_id in
                                  RaceClass.query.order_by('name')]
    if form.validate_on_submit():
        year = form.year.data
        race_class_id = form.race_class_id.data
        standings_type = form.standings_type.data
        results, race_calendar = generate_standings(year, race_class_id,\
                                                    standings_type)
        return render_template('standings.html', form=form, results=results,
                               standings_type=standings_type,\
                               race_calendar=race_calendar)

    return render_template('standings.html', form=form, results=None)


@main.route('/feedback/', methods=['GET', 'POST'])
def send_feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        name = form.name.data
        replyaddress = form.replyaddress.data
        subject = form.subject.data
        feedback = form.feedback.data
        send_feedback_email(name, replyaddress, subject, feedback)
        flash('Feedback sent!')
        return redirect(url_for('main.index'))
    return render_template('feedback.html', form=form)


@main.route('/robots.txt')
def serve_static():
    return current_app.send_static_file('robots.txt')

