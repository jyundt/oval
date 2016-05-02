from flask import Blueprint

race_class = Blueprint('race_class', __name__)

from . import views
from ..main import errors
