import requests
from flask import render_template, redirect, url_for, current_app, flash
from sqlalchemy import extract, func, and_
from ..models import RaceClass, Racer, Team, Race,\
    Participant
from ..email import send_feedback_email
from . import main
from .forms import StandingsSearchForm, FeedbackForm

#The goal of this function is return a table for the current standings for
#a given season
#e.g. Place Name Team Points
def generate_standings(year, race_class_id, standings_type):
    if standings_type == 'team':
        results = Team.query.with_entities(Team.name,
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

    elif standings_type == 'individual':
        results = Racer.query.with_entities(Racer.name,
                                            func.sum(Participant.points),\
                                            Racer.id)\
                             .join(Participant)\
                             .join(Race)\
                             .join(RaceClass)\
                             .group_by(Racer.id)\
                             .filter(and_(Race.class_id == race_class_id,\
                                          extract('year', Race.date) == year))\
                             .having(func.sum(Participant.points) > 0)\
                             .order_by(func.sum(Participant.points)\
                             .desc()).all()

    elif standings_type == 'mar':
        results = Racer.query.with_entities(Racer.name,
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
    else:
        results = None

    return results

@main.route('/')
def index():
    #Let's hard code the categories that we'd like to see on the front page
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
        results = generate_standings(year, race_class_id, standings_type)
        return render_template('standings.html', form=form, results=results,
                               standings_type=standings_type)
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
        #This is clunky, but I'm going to also add the feedback to a gdoc
        url = 'https://docs.google.com/forms/u/0/d/\
               1zIzQcf-T-R15LBZXTekcOXtD-DuBthlTBX_W4KZXId8/formResponse'
        form_data = {'entry.1964141134': name,
                     'entry.768109921':replyaddress,
                     'entry.994423798':subject,
                     'entry.282921535': feedback,
                     'draftResponse':[],
                     'pageHistory':0}
        user_agent = {'Referer':'https://docs.google.com/forms/d/\
                                 1zIzQcf-T-R15LBZXTekcOXtD-DuBthlTBX_W4KZXId8/\
                                 viewform',
                      'User-Agent':"Mozilla/5.0 (X11; Linux i686)\
                                    AppleWebKit/537.36 (KHTML, like Gecko)\
                                    Chrome/28.0.1500.52 Safari/537.36"}

        resp = requests.post(url, data=form_data, headers=user_agent)
        flash('Feedback sent!')
        return redirect(url_for('main.index'))
    return render_template('feedback.html', form=form)

@main.route('/robots.txt')
def serve_static():
    return current_app.send_static_file('robots.txt')

