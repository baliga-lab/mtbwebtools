from flask import Flask, Blueprint
from flask.ext.sqlalchemy import SQLAlchemy
import os
import os.path as op

# Initialize app
app = Flask(__name__)
app.debug = True
app.config.from_object('config')
#os.environ['PYTHON_EGG_CACHE'] = '/tmp/tmp2'
#db = SQLAlchemy(app)

from werkzeug.exceptions import default_exceptions, HTTPException
from app.views import error_handler
for exception in default_exceptions:
	app.register_error_handler(exception, error_handler)

from app.views import mod as mainModule
app.register_blueprint(mainModule)


#  For full text search
#import flask.ext.whooshalchemy as whooshalchemy
#from models import File, Gene, Condition

#whooshalchemy.whoosh_index(app, File)
#whooshalchemy.whoosh_index(app, Gene)
#whooshalchemy.whoosh_index(app, Condition)
