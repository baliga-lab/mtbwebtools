from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.admin.contrib.fileadmin import FileAdmin
import os
import os.path as op
from flask.ext.login import LoginManager
from config import basedir

from flask.ext.openid import OpenID
#from openid.extensions import pape

#import simple_openid
#from simple_openid import SimpleOpenID

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Initialize app
app = Flask(__name__)
app.debug = True
app.config.from_object('config')
db = SQLAlchemy(app)

#  For simple open id
#openid = SimpleOpenID(app, secret=app.config['SECRET_KEY'], login_url='login.html')

lm = LoginManager()
lm.init_app(app)

oid = OpenID(app, app.config['OPENID_FS_STORE_PATH'])
"""
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()
"""

#  Admin interface

from app import views, models
from models import UserAdmin, User, AdminUpload #, Role

admin = Admin(app)
admin.add_view(UserAdmin(User, db.session))
path = op.join(op.dirname(__file__), 'mtu_data')
admin.add_view(FileAdmin(path, '/mtu_data', name='Mtb Data'))

#  For full text search

import flask.ext.whooshalchemy as whooshalchemy
from models import File, Gene, Condition

whooshalchemy.whoosh_index(app, File)
whooshalchemy.whoosh_index(app, Gene)
whooshalchemy.whoosh_index(app, Condition)
