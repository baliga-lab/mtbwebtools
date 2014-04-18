from app import db#, app#, Base
from flask.ext.admin.contrib import sqla
from flask.ext.admin.contrib.sqla import filters
from flask.ext import admin
from flask.ext.admin.form.upload import FileUploadField
from flask.ext.admin import form, BaseView

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(60))
    email = db.Column(db.String(200))
    openid = db.Column(db.String(200))
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    #files = db.relationship('File', backref='user', lazy='dynamic', uselist=True)

    def __init__(self, email, fullname, role):
        self.fullname = fullname
        self.email = email
        self.role = role

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.fullname)

class UserInfo(db.Model):
    __tablename__ = 'userinfo'
    id = db.Column(db.Integer, primary_key=True)

    key = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(64))

    user_id = db.Column(db.Integer(), db.ForeignKey(User.id))
    user = db.relationship(User, backref='info')

    def __str__(self):
        return '%s - %s' % (self.key, self.value)

# Customized User model admin

class UserAdmin(sqla.ModelView):
    inline_models = (UserInfo,)

    def is_accessible(self):
        return current_user.is_authenticated() and current_user.has_role('admin')

import os.path as op

def prefix_name(obj, file_data):
    parts = op.splitext(file_data.filename)
    return secure_filename('file-%s%s' % parts)

class AdminUpload(form.BaseForm):
    upload = FileUploadField('File', namegen=prefix_name)

#  File refers to an Rdata file
class File(db.Model):
    __tablename__ = 'files'
    __searchable__ = ['expname']

    id = db.Column(db.Integer(), primary_key=True)
    filename = db.Column(db.String(100), unique=True)
    location = db.Column(db.String(500), unique=False)
    filedescr = db.Column(db.String(100), unique=False)
    expname = db.Column(db.String(500), unique=False)
    loaded = db.Column(db.Boolean, unique=False)
    #user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))

    genes = db.relationship('Gene', backref='files', lazy='dynamic', uselist=True)

    def __init__(self, filename=None, location=None, filedescr=None, expname=None, user_id=None, loaded=False):
        self.filename = filename
        self.location = location
        self. filedescr = filedescr
        self.expname = expname
        self.user_id = user_id
        self.loaded = loaded

    def get_loc(self):
        return self.location

    def get_id(self):
        return unicode(self.id)

    def is_loaded(self):
        return self.loaded

    def set_loaded(self):
        self.loaded = True

    def get_expdescr(self):
        return self.expname

    def get_genes(self):
        return self.genes

    def __repr__(self):
        return '%s' % self.filename

#  Model for ratios data from Rdata Mtu file - Gene and Linked conditions

class Gene(db.Model):
    __tablename__ = 'genes'
    __searchable__ = ['descr'] # lowercase gene name for searching purposes

    id = db.Column(db.Integer(), primary_key = True)
    #name = db.Column(db.String(200), unique=False) # for gene name, not converted to lowercase
    descr = db.Column(db.String(500), unique=False)
    file_id = db.Column(db.Integer(), db.ForeignKey('files.id')) #  Reference back to an file id

    conditions = db.relationship('Condition', backref = 'genes', lazy = 'dynamic', uselist=True)

    def __init__(self, descr=None, file_id=None):#, name=None):
        self.descr = descr
        #self.name = name
        self.file_id = file_id

    def get_id(self):
        return unicode(self.id)

    def get_conditions(self):
        return self.conditions

    def __repr__(self):
        return "<Gene %s>" % (self.descr)

    def __str__(self):
        return unicode(self.id)

class Condition(db.Model):
    __tablename__ = 'conditions'

    __searchable__ = ['condition','annot1','annot2','annot3']

    id = db.Column(db.Integer(), primary_key = True)
    condition = db.Column(db.String(500), unique=False)
    replicate = db.Column(db.String(200), unique=False)
    value = db.Column(db.String(150))
    annot1 = db.Column(db.String(500))
    annot2 = db.Column(db.String(500))
    annot3 = db.Column(db.String(500))

    gene_id = db.Column(db.Integer(), db.ForeignKey('genes.id'))

    def __init__(self, condition, value, gene_id, replicate, annot1, annot2, annot3):
        self.condition = condition
        self.value = value
        self.gene_id = gene_id
        self.replicate = replicate
        self.annot1 = annot1
        self.annot2 = annot2
        self.annot3 = annot3

    def get_id(self):
        return unicode(self.id)

    def get_replicate(self):
        return unicode(self.replicate)

    def get_value(self):
        return unicode(self.value)

    def get_condition(self):
        return self.condition

    def get_annots(self):
        return [unicode(self.annot1),unicode(self.annot2),unicode(self.annot3)]

    def __repr__(self):
        return "<Condition %s>" % (self.condition)

    def __str__(self):
        return unicode(self.condition)





