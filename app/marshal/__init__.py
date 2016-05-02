from flask import Blueprint

marshal = Blueprint('marshal', __name__)

from . import views
from ..main import errors
