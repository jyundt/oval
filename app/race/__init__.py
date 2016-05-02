from flask import Blueprint

race = Blueprint('race', __name__)

from . import views
from ..main import errors
