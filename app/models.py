from database import Base
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship, backref

#  File refers to an Rdata file
class File(Base):
#class File(Base):
    __tablename__ = 'files'
    __searchable__ = ['expname']

    id = Column(Integer(), primary_key=True)
    filename = Column(String(100), unique=True)
    location = Column(String(500), unique=False)
    filedescr = Column(String(100), unique=False)
    expname = Column(String(500), unique=False)
    loaded = Column(Boolean, unique=False)
    #user_id = Column(Integer(), ForeignKey('user.id'))

    genes = relationship('Gene', backref='files', lazy='dynamic', uselist=True)

    def __init__(self, filename=None, location=None, filedescr=None, expname=None, user_id=None, loaded=False):
        self.filename = filename
        self.location = location
        self.filedescr = filedescr
        self.expname = expname
        #self.user_id = user_id
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

class Gene(Base):
#class Gene(Base):
    __tablename__ = 'genes'
    __searchable__ = ['descr'] # lowercase gene name for searching purposes

    id = Column(Integer(), primary_key = True)
    #name = Column(String(200), unique=False) # for gene name, not converted to lowercase
    descr = Column(String(500), unique=False)
    file_id = Column(Integer(), ForeignKey('files.id')) #  Reference back to an file id

    conditions = relationship('Condition', backref = 'genes', lazy = 'dynamic', uselist=True)

    def __init__(self, descr=None, file_id=None):
        self.descr = descr
        self.file_id = file_id

    def get_id(self):
        return unicode(self.id)

    def get_conditions(self):
        return self.conditions

    def __repr__(self):
        return "<Gene %s>" % (self.descr)

    def __str__(self):
        return unicode(self.id)

class Condition(Base):
#class Condition(Base):
    __tablename__ = 'conditions'

    __searchable__ = ['condition','annot1','annot2','annot3']

    id = Column(Integer(), primary_key = True)
    condition = Column(String(500), unique=False)
    replicate = Column(String(200), unique=False)
    value = Column(String(150))
    annot1 = Column(String(500))
    annot2 = Column(String(500))
    annot3 = Column(String(500))

    gene_id = Column(Integer(), ForeignKey('genes.id'))

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





