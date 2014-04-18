#A config.py file must be created like: 
import os SECRET_KEY = 'something-mysterious' 
DEBUG = True 
BASEDIR = os.path.abspath(os.path.dirname(file)) 
DATA_FOLDER = '/app/static/datafiles/' 
SQLALCHEMY_DATABASE_URI = 'mysql://root@/mtbflask' 
SQLALCHEMY_MIGRATE_REPO = os.path.join(BASEDIR, 'db_repository') 
WHOOSH_BASE = os.path.join(BASEDIR, 'search.db')
