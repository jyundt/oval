from flask import render_template

from . import stats


@stats.route('/')
def index():
    return render_template('stats/index.html')
