mtbwebtools
===========

A python flask webapp for exploring cMonkey and curation results (for Tb).

Module Requirements:

Flask==0.10.1
Flask-SQLAlchemy==0.16
Flask-WTF==0.9.4
Flask-WhooshAlchemy==0.54a
Jinja2==2.7.2
SQLAlchemy==0.8.2
WTForms==1.0.5
Werkzeug==0.9.4
Whoosh==2.5.6
numpy
scipy
simplejson
sqlalchemy-migrate==0.8.2

A config.py file must be created like:\n
import os\n
SECRET_KEY = 'something-mysterious'\n
DEBUG = True\n
BASEDIR = os.path.abspath(os.path.dirname(__file__))\n
DATA_FOLDER = '<your base folder>/app/static/datafiles/'\n
SQLALCHEMY_DATABASE_URI = 'mysql://root@<yourserver>/mtbflask'\n
SQLALCHEMY_MIGRATE_REPO = os.path.join(BASEDIR, 'db_repository')\n
WHOOSH_BASE = os.path.join(BASEDIR, 'search.db')\n
