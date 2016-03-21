from flask import Blueprint

main = Blueprint('main', __name__)

#I don't have custom error pages yet
#from . import views, errors
from . import views
