from flask import Blueprint

stats = Blueprint('stats', __name__)

from . import views
