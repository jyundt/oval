from collections import OrderedDict
from itertools import groupby
from operator import itemgetter, and_

import datetime
from ranking import Ranking

from flask import render_template, redirect, request, url_for, current_app, flash
from sqlalchemy import extract, or_
from sqlalchemy import func

from app import db
from . import main
from .forms import FeedbackForm
from ..email import send_feedback_email
from ..models import Course, RaceClass, Racer, Team, Race, Participant

from slackclient import SlackClient


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


def _make_result(name, id_, rank, total_pts, pts, race_calendar, team_name, team_id):
    """Create result dictionary to make html templates more readable
    """
    result = {"name": name,
              "id": id_,
              "rank": rank,
              "total_pts": total_pts,
              "race_pts": OrderedDict([(date, "-") for date,_ in race_calendar]),
              "team_name": team_name,
              "team_id": team_id}

    for point, date in pts:
        if point:
            result["race_pts"][date] = point

    return result


def _sort_and_rank(items, key):
    return Ranking(sorted(items, key=key, reverse=True), key=key, start=1)


def _gen_team_standings(race_info, race_calendar):
    """Return team standings with individual race and total points
    """
    # Sort race info first by team (for grouping below) then by date
    # for table construction.  Filter results not associated with a team.
    team_race_info = sorted(
        [ri for ri in race_info if ri.team_id],
        key=lambda ri: (ri.team_id, ri.race_date))

    def sum_team_points_by_date(team_results):
        return [
            (sum(ri.team_points or 0 for ri in dg), date)
            for (team_id, date), dg in
            groupby(team_results, key=lambda ri: (ri.team_id, ri.race_date))]
    team_points_by_date = {
        team_id: sum_team_points_by_date(g) for team_id, g
        in groupby(team_race_info, key=lambda ri: ri.team_id)}

    # Aggregate results by team
    team_agg_info = [
        (team_id, team_name, sum(ri.team_points or 0 for ri in g))
        for ((team_id, team_name), g) in
        groupby(team_race_info, key=lambda ri: (ri.team_id, ri.team_name))
    ]

    # Filter to only teams that have points, and
    # rank by total team points.
    ranked_teams = _sort_and_rank(
        filter(itemgetter(2), team_agg_info),
        key=itemgetter(2))

    results = []
    for rank, (team_id, team_name, total_pts) in ranked_teams:
        result = _make_result(name=team_name, id_=team_id, rank=rank, total_pts=total_pts,
                              pts=team_points_by_date[team_id], race_calendar=race_calendar,
                              team_name=None, team_id=None)
        results.append(result)
    return results


def _gen_ind_standings(race_info, race_calendar):
    """Return top individual racer standings with individual race and total points

    Note, individual placing tiebreak is by number of wins, followed by number of
    seconds places, etc.
    """
    # Sort race info first by racer (for grouping below) then by date
    # for table construction.
    racer_race_info = sorted(race_info, key=lambda ri: (ri.racer_id, ri.race_date))

    # A list of per-race points for each racer
    racer_race_points = {
        racer_id: list((ri.points, ri.race_date) for ri in g)
        for racer_id, g in groupby(racer_race_info, key=lambda ri: ri.racer_id)}

    # Team info for each racer
    racer_teams = {
        racer_id: [(ri.team_name, ri.team_id) for ri in g]
        for racer_id, g in groupby(racer_race_info, key=lambda ri: ri.racer_id)
    }

    def placing_counts(placings):
        # Helper to count placings
        # Returns a tuple with the count of number of first places, then number
        # of seconds, etc., up to the 8th place.
        placings = filter(None, placings)
        if not placings:
            return ()
        counts_by_place = {place: sum(1 for _ in g) for place, g in groupby(sorted(placings))}
        assert min(counts_by_place.keys()) >= 1
        return tuple(counts_by_place.get(place) or 0 for place in xrange(1, 9))

    # Group race results by racer
    race_info_gby_racer = [
        ((racer_id, racer_name), list(g))
        for ((racer_id, racer_name), g) in
        groupby(racer_race_info, key=lambda ri: (ri.racer_id, ri.racer_name))]

    # Aggregate points and placings by racer
    racer_agg_info = [(
            racer_id,
            racer_name,
            sum(r.points or 0 for r in g),
            placing_counts(r.place for r in g))
        for (racer_id, racer_name), g in race_info_gby_racer]

    # Filter to only racers that have any points,
    # rank by total points then by placings.
    ranked_racers = _sort_and_rank(
        filter(itemgetter(2), racer_agg_info),
        key=itemgetter(2, 3))

    results = []
    for rank, (racer_id, racer_name, racer_points, _) in ranked_racers:
        team = racer_teams[racer_id][0] if racer_id in racer_teams else (None, None)
        result = _make_result(name=racer_name, id_=racer_id, rank=rank, total_pts=racer_points,
                              pts=racer_race_points[racer_id], race_calendar=race_calendar,
                              team_name=team[0], team_id=team[1])
        results.append(result)
    return results


def _gen_mar_standings(race_info, race_calendar):
    """Return top MAR standings with individual race and total points
    """
    # Sort race info first by racer (for grouping below) then by date
    # for table construction.
    racer_race_info = sorted(race_info, key=lambda ri: (ri.racer_id, ri.race_date))

    # A list of per-race mar points for each racer
    racer_race_mar_points = {
        racer_id: list((ri.mar_points, ri.race_date) for ri in g)
        for racer_id, g in groupby(racer_race_info, key=lambda ri: ri.racer_id)}

    # Team info for each racer
    racer_teams = {
        racer_id: list((ri.team_name, ri.team_id) for ri in g)
        for racer_id, g in groupby(racer_race_info, key=itemgetter(0))
    }

    # Aggregate mar points by racer
    racer_agg_info = [
        (racer_id, racer_name, sum(ri.mar_points or 0 for ri in g))
        for (racer_id, racer_name), g in
        groupby(racer_race_info, key=lambda ri: (ri.racer_id, ri.racer_name))]

    # Filter to only racers that have any mar points,
    # rank by total points.
    ranked_racers = _sort_and_rank(
        filter(itemgetter(2), racer_agg_info),
        key=itemgetter(2))

    results = []
    for rank, (racer_id, racer_name, racer_points) in ranked_racers:
        team = racer_teams[racer_id][0] if racer_id in racer_teams else (None, None)
        result = _make_result(name=racer_name, id_=racer_id, rank=rank, total_pts=racer_points,
                              pts=racer_race_mar_points[racer_id], race_calendar=race_calendar,
                              team_name=team[0], team_id=team[1])
        results.append(result)
    return results


@main.route('/')
def index():
    """Fills and renders the front page index.html template
    
    Only display recent results when they're within the past ~three months.
    """
    recent_time = datetime.datetime.now() - datetime.timedelta(days=90)
    recent_results = (
        Race.query
        .join(Participant, Race.id == Participant.race_id)
        .filter(Race.date > recent_time)
        .group_by(Race.id)
        .having(func.count(Participant.id) > 0))
    r1 = recent_results.subquery('r1')
    r2 = recent_results.subquery('r2')
    latest_races = (
        db.session.query(r1)
        .with_entities(
            r1.c.id.label('id'),
            r1.c.date.label('date'),
            RaceClass.name.label('class_name'))
        .join(r2, and_(r1.c.class_id == r2.c.class_id, r1.c.date < r2.c.date), isouter=True)
        .join(RaceClass, RaceClass.id == r1.c.class_id)
        .filter(r2.c.id.is_(None)))
    races = latest_races.all()
    return render_template('index.html', races=races)


@main.route('/standings/')
def standings():
    years = sorted(set(
        int(date.year) for (date,) in Race.query.with_entities(Race.date)
                                                .filter_by(points_race=True)),
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
        .join(Participant)
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
                Racer.id.label('racer_id'), Racer.name.label('racer_name'),
                Race.date.label('race_date'), Participant.points,
                Participant.team_points, Participant.mar_points,
                Team.id.label('team_id'), Team.name.label('team_name'), Participant.place)
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

    return render_template('standings.html', selected_year=year, years=years)


@main.route('/results/')
def results():
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
        race_info = (Racer.query.with_entities(
            Racer.id, Racer.name,
            Team.id, Team.name,
            Participant.place, Participant.mar_place,
            Race.id, Race.date,
            Race.course_id, Race.average_lap, Race.fast_lap,
            Race.winning_time, Race.laps, Race.starters, Race.points_race,
            RaceClass.id, RaceClass.name,
            Course.name, Course.length_miles)
            .join(Participant, Participant.racer_id == Racer.id)
            .join(Team, Team.id == Participant.team_id, isouter=True)
            .join(Race, Race.id == Participant.race_id)
            .join(RaceClass, RaceClass.id == Race.class_id)
            .join(Course, Course.id == Race.course_id)
            .filter(or_(Participant.place == 1, Participant.mar_place == 1))
            .filter(extract("year", Race.date) == year)
            .filter(Race.class_id == race_class_id)
            .order_by(Race.date)
            .all())

        race_info_by_date = [
            (date, list(date_group))
            for date, date_group in groupby(race_info, key=itemgetter(7))]
        results = []
        for date, date_group in race_info_by_date:
            (race_id, race_date, course_id, average_lap, fast_lap, winning_time,
                laps, starters, points_race, race_class_id, race_class_name,
                course_name, course_length_miles) = date_group[0][6:]
            winner = None
            mar_winner = None
            for maybe_winner in date_group:
                racer_id, racer_name, team_id, team_name, place, mar_place = maybe_winner[0:6]
                if place == 1:
                    winner = (racer_id, racer_name, team_id, team_name)
                if mar_place == 1:
                    mar_winner = (racer_id, racer_name, team_id, team_name)
            avg_lap = (average_lap.total_seconds()) if average_lap else (
                (winning_time.total_seconds() / laps)
                if (winning_time and laps) else None)
            avg_speed = (
                course_length_miles / (avg_lap / 3600)
                if course_length_miles and avg_lap
                else None)
            results.insert(0, {
                'race_id': race_id,
                'date': date,
                'course_name': course_name,
                'winner': winner,
                'mar_winner': mar_winner,
                'fast_lap': fast_lap,
                'avg_speed': avg_speed,
                'starters': starters,
                'points_race': points_race})

        return render_template(
            'results.html',
            selected_year=year, selected_race_class_id=race_class_id,
            years=years, race_classes=race_classes, results=results)

    return render_template('results.html', results=None)


@main.route('/feedback/', methods=['GET', 'POST'])
def send_feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        name = form.name.data
        replyaddress = form.replyaddress.data
        subject = form.subject.data
        feedback = form.feedback.data
        send_feedback_email(name, replyaddress, subject, feedback)
        message = "%s <%s> - %s: %s" % (name, replyaddress, subject, feedback)
        token = current_app.config['SLACK_OAUTH_API_TOKEN']
        sc = SlackClient(token)
        sc.api_call("chat.postMessage", channel="#feedback", text=message,
                    username="Flask")
        flash('Feedback sent!')
        return redirect(url_for('main.index'))
    return render_template('feedback.html', form=form)


@main.route('/robots.txt')
def serve_static():
    return current_app.send_static_file('robots.txt')

