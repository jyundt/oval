from flask import Blueprint

team = Blueprint('team', __name__)

from . import views
from ..main import errors
