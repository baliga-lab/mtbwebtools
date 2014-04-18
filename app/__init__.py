from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
import os
import os.path as op

# Initialize app
app = Flask(__name__)
app.debug = True
app.config.from_object('config')
os.environ['PYTHON_EGG_CACHE'] = '/tmp/tmp2'
db = SQLAlchemy(app)

#mtb = Blueprint('mtb', __name__, template_folder='templates')
#app.register_blueprint(mtb)

from app.views import mod as mainModule
app.register_blueprint(mainModule)

#  For full text search
#from app import views, models
import flask.ext.whooshalchemy as whooshalchemy
from models import File, Gene, Condition

whooshalchemy.whoosh_index(app, File)
whooshalchemy.whoosh_index(app, Gene)
whooshalchemy.whoosh_index(app, Condition)