from flask import Blueprint

official = Blueprint('official', __name__)

from . import views
from ..main import errors
