from flask import Blueprint

results = Blueprint('results', __name__)

from . import views
