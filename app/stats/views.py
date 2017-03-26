import datetime
from flask import render_template, request
from ranking import Ranking
from sqlalchemy import case
from sqlalchemy import func

from . import stats
from ..models import Race, Racer, Participant, RaceClass


@stats.route('/')
def index():
    race_classes = [
        (race_class_id.id, race_class_id.name)
        for race_class_id in
        RaceClass.query.with_entities(
            RaceClass.id, RaceClass.name)
        .join(Race)
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

    earliest_date_qr = (
        Race.query
        .filter(Race.class_id == race_class_id)
        .order_by(Race.date)
        .limit(1)).one_or_none()
    earliest_date = earliest_date_qr.date if earliest_date_qr else datetime.date.today()

    individual_points = [
        {'racer_id': r.racer_id, 'racer_name': r.racer_name, 'rank': rank, 'points': r.points}
        for rank, r in Ranking(
            Racer.query.with_entities(
                Racer.id.label('racer_id'), Racer.name.label('racer_name'),
                func.sum(Participant.points).label('points'))
            .join(Participant, Participant.racer_id == Racer.id)
            .join(Race, Race.id == Participant.race_id)
            .filter(Race.points_race)
            .filter(Race.class_id == race_class_id)
            .group_by(Racer.id)
            .having(func.sum(Participant.points) > 0)
            .order_by(func.sum(Participant.points).desc()),
            key=lambda r: r.points, start=1)]

    mar_points = [
        {'racer_id': r.racer_id, 'racer_name': r.racer_name, 'rank': rank, 'mar_points': r.mar_points}
        for rank, r in Ranking(
            Racer.query.with_entities(
                Racer.id.label('racer_id'), Racer.name.label('racer_name'),
                func.sum(Participant.mar_points).label('mar_points'))
            .join(Participant, Participant.racer_id == Racer.id)
            .join(Race, Race.id == Participant.race_id)
            .filter(Race.points_race)
            .filter(Race.class_id == race_class_id)
            .group_by(Racer.id)
            .having(func.sum(Participant.mar_points) > 0)
            .order_by(func.sum(Participant.mar_points).desc()),
            key=lambda r: r.mar_points, start=1)]

    wins = [{
        'racer_id': r.racer_id, 'racer_name': r.racer_name, 'rank': rank,
        'wins': r.wins, 'points_wins': r.points_wins}
        for rank, r in Ranking(
            Racer.query.with_entities(
                Racer.id.label('racer_id'), Racer.name.label('racer_name'),
                func.count(1).label('wins'),
                func.sum(case([(Race.points_race, 1)], else_=0)).label('points_wins'))
            .join(Participant, Participant.racer_id == Racer.id)
            .join(Race, Race.id == Participant.race_id)
            .filter(Race.class_id == race_class_id)
            .filter(Participant.place == 1)
            .group_by(Racer.id)
            .order_by(
                func.count(1).label('wins').desc(),
                func.sum(case([(Race.points_race, 1)], else_=0)).desc()),
            key=lambda r: r.wins, start=1)]

    trifectas = (
        Racer.query.with_entities(
            Racer.id.label('racer_id'), Racer.name.label('racer_name'),
            Race.id.label('race_id'), Race.date.label('race_date'))
        .join(Participant, Participant.racer_id == Racer.id)
        .join(Race, Race.id == Participant.race_id)
        .filter(Participant.place == 1)
        .filter(Participant.mar_place == 1)
        .filter(Participant.point_prime)
        .filter(Race.class_id == race_class_id)
        .order_by(Race.date)).all()

    return render_template(
        'stats/index.html', selected_race_class_id=race_class_id,
        race_classes=race_classes, earliest_date=earliest_date,
        individual_points=individual_points, mar_points=mar_points,
        wins=wins, trifectas=trifectas)
