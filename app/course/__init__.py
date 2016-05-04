from flask import Blueprint

course = Blueprint('course', __name__)

from . import views
from ..main import errors
