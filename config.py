import os
#from flask_openid import COMMON_PROVIDERS

SECRET_KEY = 'you-will-never-guess'
DEBUG = True

basedir = os.path.abspath(os.path.dirname(__file__))

BASEDIR = os.path.abspath(os.path.dirname(__file__))

ALLOWED_EXTENSIONS = set(['RData', 'csv'])
DATA_FOLDER = '/local/htdocs/mtbwebtools/app/static/datafiles/'

SQLALCHEMY_DATABASE_URI = 'mysql://root@como/mtbflask'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

WHOOSH_BASE = os.path.join(basedir, 'search.db')
