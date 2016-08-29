from collections import OrderedDict
from itertools import groupby
from operator import itemgetter

from flask import render_template, redirect, request, url_for, current_app, flash
from sqlalchemy import extract

from . import main
from .forms import FeedbackForm
from ..email import send_feedback_email
from ..models import RaceClass, Racer, Team, Race, Participant


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


def _gen_team_standings(race_info, race_calendar):
    """Return team standings with individual race and total points
    """
    # team_id, team_name, team_points, date
    team_race_info = sorted(
        filter(itemgetter(0), map(itemgetter(6, 7, 4, 2), race_info)),
        key=itemgetter(0, 3))

    # team_id, team_name, total_team_points
    teams = sorted(filter(itemgetter(2), [
        (team_id, team_name, sum(team_points or 0 for team_id, team_name, team_points, _ in g))
        for (team_id, team_name), g in groupby(team_race_info, key=itemgetter(0, 1))]),
        key=itemgetter(2), reverse=True)

    def sum_team_points_by_date(team_results):
        return [
            (sum(team_points or 0 for _, _, team_points, _ in dg), date)
            for (team_id, date), dg in groupby(team_results, key=itemgetter(0, 3))]
    team_points_by_date = {
        team_id: sum_team_points_by_date(g) for team_id, g
        in groupby(team_race_info, key=itemgetter(0))}

    results = []
    for team_id, team_name, total_pts in teams:
        result = _make_result(name=team_name, id_=team_id, total_pts=total_pts,
                              pts=team_points_by_date[team_id], race_calendar=race_calendar,
                              team_name=None, team_id=None)
        results.append(result)
    return results


def _gen_ind_standings(race_info, race_calendar):
    """Return top individual racer standings with individual race and total points
    """

    # racer_id, racer_name, race_date, points, team_id, team_name
    racer_race_info = sorted(
        map(itemgetter(0, 1, 2, 3, 6, 7), race_info),
        key=itemgetter(0, 2))
    racer_race_points = {
        racer_id: list((points, date) for _, _, date, points, _, _ in g)
        for racer_id, g in groupby(racer_race_info, key=itemgetter(0))}
    racers = sorted(filter(itemgetter(2), [
        (racer_id, racer_name, sum(points or 0 for _, _, _, points, _, _ in g))
        for (racer_id, racer_name), g in groupby(racer_race_info, key=itemgetter(0, 1))]),
        key=itemgetter(2), reverse=True)
    racer_teams = {
        racer_id: list((team_name, team_id) for _, _, _, _, team_id, team_name in g)
        for racer_id, g in groupby(racer_race_info, key=itemgetter(0))
    }

    results = []
    for racer_id, racer_name, racer_points in racers:
        team = racer_teams[racer_id][0] if racer_id in racer_teams else (None, None)
        result = _make_result(name=racer_name, id_=racer_id, total_pts=racer_points,
                              pts=racer_race_points[racer_id], race_calendar=race_calendar,
                              team_name=team[0], team_id=team[1])
        results.append(result)
    return results


def _gen_mar_standings(race_info, race_calendar):
    """Return top MAR standings with individual race and total points
    """
    # racer_id, racer_name, race_date,  mar_points, team_id, team_name
    racer_race_info = sorted(
        map(itemgetter(0, 1, 2, 5, 6, 7), race_info),
        key=itemgetter(0, 2))
    racer_race_mar_points = {
        racer_id: list((mar_points, date) for _, _, date, mar_points, _, _ in g)
        for racer_id, g in groupby(racer_race_info, key=itemgetter(0))}
    racers = sorted(filter(itemgetter(2), [
        (racer_id, racer_name, sum(mar_points or 0 for _, _, _, mar_points, _, _ in g))
        for (racer_id, racer_name), g in groupby(racer_race_info, key=itemgetter(0, 1))]),
        key=itemgetter(2), reverse=True)
    racer_teams = {
        racer_id: list((team_name, team_id) for _, _, _, _, team_id, team_name in g)
        for racer_id, g in groupby(racer_race_info, key=itemgetter(0))
    }

    results = []
    for racer_id, racer_name, racer_points in racers:
        team = racer_teams[racer_id][0] if racer_id in racer_teams else (None, None)
        result = _make_result(name=racer_name, id_=racer_id, total_pts=racer_points,
                              pts=racer_race_mar_points[racer_id], race_calendar=race_calendar,
                              team_name=team[0], team_id=team[1])
        results.append(result)
    return results


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


@main.route('/standings/')
def standings():
    years = sorted(set(
        int(date.year) for (date,) in Race.query.with_entities(Race.date).all()),
        reverse=True)
    try:
        req_year = int(request.args.get('year'))
    except (ValueError, TypeError):
        req_year = None
    year = req_year if req_year is not None else (years[0] if years else None)

    race_classes = [
        (race_class_id.id, race_class_id.name)
        for race_class_id in
        RaceClass.query.with_entities(
            RaceClass.id, RaceClass.name)
        .join(Race)
        .filter(extract("year", Race.date) == year)
        .filter(Race.points_race == True)
        .group_by(RaceClass.id)
        .order_by(RaceClass.name)]
    year_race_class_ids = [race_class_id for race_class_id, _ in race_classes]
    try:
        req_race_class_id = int(request.args.get('race_class_id'))
    except (ValueError, TypeError):
        req_race_class_id = None
    race_class_id = (
        req_race_class_id if req_race_class_id in year_race_class_ids
        else (year_race_class_ids[0] if year_race_class_ids else None))

    if year is not None and race_class_id is not None:
        race_info = (
            Racer.query.with_entities(
                Racer.id, Racer.name, Race.date,
                Participant.points, Participant.team_points, Participant.mar_points,
                Team.id, Team.name)
                .join(Participant)
                .join(Team, isouter=True)
                .join(Race)
                .filter(Race.points_race == True)
                .filter(extract("year", Race.date) == year)
                .filter(Race.class_id == race_class_id)
                .order_by(Racer.id, Race.date.desc())
                .all())
        race_calendar = _gen_race_calendar(year, race_class_id)
        ind_standings = _gen_ind_standings(race_info, race_calendar)
        team_standings = _gen_team_standings(race_info, race_calendar)
        mar_standings = _gen_mar_standings(race_info, race_calendar)
        results = (
            ('Individual', ind_standings),
            ('Team', team_standings),
            ('MAR', mar_standings))
        return render_template(
            'standings.html',
            selected_year=year, selected_race_class_id=race_class_id,
            years=years, race_classes=race_classes,
            results=results, race_calendar=race_calendar)

    return render_template('standings.html', results=None)


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

