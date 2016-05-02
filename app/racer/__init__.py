from flask import Blueprint

racer = Blueprint('racer', __name__)

from . import views
from ..main import errors
