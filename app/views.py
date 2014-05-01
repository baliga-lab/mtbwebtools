from flask import render_template, flash, redirect, url_for, request, g, make_response, send_from_directory, Blueprint, abort
from sqlalchemy import or_, and_
from werkzeug import secure_filename
from jinja2 import TemplateNotFound
from app import app
#from functools import wraps
from .models import File, Gene, Condition
from .forms import SearchForm

import Heatmap
from Heatmap import *

import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.colors import LinearSegmentedColormap
#import pylab as pl
#import random
#from cStringIO import StringIO
#from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#from matplotlib.figure import Figure
import StringIO

import os
import json
import codecs # For opening JSON file from R
import subprocess
import csv
import operator

mod = Blueprint('mod', __name__, template_folder='templates')

from .database import Session

def error_handler(error):
    msg = "Request resulted in {}".format(error)
    current_app.logger.warning(msg, exc_info=error)

    if isinstance(error, HTTPException):
        description = error.get_description(request.environ)
        code = error.code
        name = error.name
    else:
        description = ("We encountered an error "
                       "while trying to fulfill your request")
        code = 500
        name = 'Internal Server Error'

@mod.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

@mod.errorhandler(505)
def internal_server_error(e):
    return render_template('505.html'), 505

@mod.route('/')
@mod.route('/index')
def index():
	try:
	    return render_template('index.html',
	        title = 'Home')
	except TemplateNotFound:
		abort(404)

@mod.route('/profile')
def profile():
	db_session = Session()
	dbfiles = db_session.query(File).all()
	files=[]
	for f in dbfiles:
		files.append(f.filename)
	db_session.rollback()
	#try:
	return render_template('profile.html', files=files)
	#except HTTPException:
	#	return redirect(url_for('.internal_server_error', e=HTTPException))

###  FULL TEXT SEARCHING  ###

@mod.route('/search', methods = ['POST'])
def search():
	if request.method == 'POST':
		text = request.form['searchtext']
		return redirect(url_for('.search_results', query = text))
	return redirect(url_for('profile'))

@mod.route('/search_results/<query>')
def search_results(query):
	db_session = Session()
	dbgeneresults = db_session.query(Gene).filter(Gene.descr == query.lower()).all() #Gene.query.whoosh_search(query.lower()).all() # All genes stored as lowercase
	generesults = []
	for g in dbgeneresults:
		generesults.append(g.descr)
	dbcondresults = db_session.query(Condition).filter(or_(Condition.annot1 == query.lower(), Condition.annot2 == query.lower(), Condition.annot3 == query.lower())).all() 
	condresults = set([]) # use set to remove duplicate elements
	for c in dbcondresults:
		condresults.add(c.condition)
	expresults = db_session.query(File).filter(File.filename == query).all() #File.query.whoosh_search(query).all()
	return render_template('search_results.html',
        query = query,
        generesults = generesults,
        condresults = condresults,
        expresults = expresults)

	db_session.rollback()

###  VISUALIZATIONS  ###

@mod.route('/displays/<filename>', methods=['POST','GET'])
def displays(filename):

	db_session = Session()

	dbfile = db_session.query(File).filter_by(filename=filename).first()
	dbgenes = dbfile.get_genes()
	genelist = []
	for dbg in dbgenes:
		genelist.append(dbg.descr)
	biclusters = []
	for fname in os.listdir(os.path.join(app.config['DATA_FOLDER'],'biclusters')):
		biclusters.append(os.path.basename(fname).rsplit('.')[0].replace('bc_','')) # Get just the number
	biclusters.sort()
	biclustersstr = []
	filename_trunc = filename.split('_')[2].rsplit('.')[0] # WARNING: specific for mtu_inf results and bicluster path, see bicluster fxn below (i.e. may not work for all experiment names)
	for bc in biclusters:
		s = 'bicluster_'+makeBiclusterStr(bc) # Create the bicluster string for the drop-down menu (word 'bicluster' with leading zeros, e.g. bicluster_0001)
		biclustersstr.append(s)

	db_session.rollback()

	if request.method == 'POST':
		if request.form['submit'] == 'Zoomplot':
			return redirect(url_for('.zoomplot', fileid=dbfile.id, genedescr=request.form['select1']))
		if request.form['submit'] == 'Lineplot':
			text = request.form['text']
			textstr = toCSstring(text)
			return redirect(url_for('.d3lineplot',filename=filename, textstr=textstr))
		if request.form['submit'] == 'Heatmap':
			return redirect(url_for('.genelist', filename=filename))
		if request.form['submit'] == 'Bicluster Heatmap':
			return redirect(url_for('.bicluster', filename_trunc=filename_trunc, bicluster=request.form['selectbc']))
	return render_template('displays.html', filename=filename, geneids=genelist, biclusters=biclustersstr) 

def toCSstring(sometext):
	sometext.rstrip()
	sometext = sometext.lower()
	alist = sometext.split('\r\n')
	commastr = ",".join(alist)
	return commastr

def makeBiclusterStr(bc_num):
	wantlen = 4
	i = len(bc_num)
	bcstr = bc_num
	while i < wantlen:
		bcstr = "0"+bcstr
		i+=1
	return bcstr

#  ZOOMPLOT # -> for one gene across all conditions (non-NA)

@mod.route('/zoomplot/<fileid>/<genedescr>')
def zoomplot(fileid, genedescr):
	jsonfile = makeJSONdataZoomplot(fileid, genedescr)
	#dbgene = Gene.query.filter_by(descr=genedescr).first()
	return render_template('d3zoomplot_conds.html', jsonobj=jsonfile, genename=genedescr)

###
#  Create JSON representation of data for a gene (used by zoomplot)
###
def makeJSONdataZoomplot(fileid, genedescr):

	db_session = Session()
	gene = db_session.query(Gene).filter_by(descr=genedescr,file_id=fileid).first()
	outputfilenm = gene.descr+'_json.txt'
	fulloutput = os.path.join(app.config['DATA_FOLDER'], outputfilenm)
	if os.path.isfile(fulloutput): #  Does file already exist?  if so do not need to make it again
		return outputfilenm
	conditions = gene.get_conditions()
	cond2vals = {}
	for cond in conditions:
		dbcond = db_session.query(Condition).filter_by(condition=cond).filter_by(gene_id=gene.get_id()).first() # all replicates
		condstr = dbcond.get_condition()
		val = dbcond.get_value()
		if val =='NA':
			continue
		cond2vals[condstr] = val

		db_session.rollback()

		with open(fulloutput, 'w') as f:
			f.write(unicode(json.dumps(cond2vals, ensure_ascii=False, indent=4, separators=(',', ': '))))
		f.close()
		#jsonobj = json.dumps(cond2vals, ensure_ascii=True)
		return outputfilenm

		

	#return jsonobj


#  LINEPLOT  #  -> can view multiple genes across all conditions

@mod.route('/d3lineplot/<filename>/<textstr>')
def d3lineplot(filename, textstr):
    #genelist = parseText(text)

    db_session = Session()
    genelist = textstr.split(',')
    fstr = textstr.rstrip().replace(',','_')
    dbfile = db_session.query(File).filter_by(filename=filename).first()
    genedescrs = [x for x in genelist]
    jsonstr = '{'
    jsonstr = jsonstr+'\n\"labels\": '+json.dumps(genedescrs) + ','
    allvals = []
    ntimes = 0
    for g in genelist:
    	vals = [] # ea gene is going to have an array of values cooresponding to the conditions
    	dbgene = db_session.query(Gene).filter_by(descr=g, file_id=dbfile.id).first()
    	conds = dbgene.get_conditions()
    	for c in conds:
    		val = c.get_value()
    		vals.append(val)
    	ntimes = len(vals)
    	allvals.append(vals)
    jsonstr = jsonstr+'\n\"times\": ' + json.dumps([x for x in range(ntimes)])+','
    jsonstr = jsonstr+'\n\"curves\": '
    jsonstr=jsonstr+json.dumps(allvals)+'}'
    outfile = os.path.join(app.config['DATA_FOLDER'], 'json4lineplot_'+fstr+'.json')
    OUT = open(outfile, 'wb')
    OUT.write(jsonstr)
    db_session.rollback()
    return render_template('d3lineplot.html', jsonfile=os.path.basename(outfile))

    


#  HEATMAP FXNS  #

@mod.route('/heatmapinput/<filename>', methods=['GET','POST'])
def heatmapinput(filename):
	db_session = Session()
	dbfile = db_session.query(File).filter_by(filename=filename).first()
	db_session.rollback()


@mod.route('/heatmap/<inputdata>/<inputlabels>') #'/<pngrows>/<pngcols>')
def heatmap(inputdata, inputlabels): #, pngrows, pngcols):
	return render_template('d3heatmap.html', inputdata=inputdata, inputlabels=inputlabels) #, pngrows=pngrows, pngcols=pngcols)

@mod.route('/genelist/<filename>', methods=['GET','POST'])
def genelist(filename):
	#  Get user name from openid/email
	#uname = g.user.email.split('@')[0]
	#dbfilename = os.path.join(app.config['DATA_FOLDER'], (filename.rsplit('.', 1)[0]+'.csv'))
	#dbfile = File.query.filter_by(filename=os.path.basename(dbfilename)).first()
	db_session = Session()
	dbfile = db_session.query(File).filter_by(filename=filename).first()


	if dbfile is None:
		db_session.close()
		flash('can not find dbfile '+filename)
		return redirect(url_for('.profile'))

	#  File name for annotfile, check if exits, if not make it, then read in the annots
	annotoutfile = os.path.join(app.config['DATA_FOLDER'], 'All_annots_'+dbfile.filename.rsplit('.',1)[0]+'.txt')
	allannots = []
	if not os.path.isfile(annotoutfile):
		getAllAnnots(filename)

	with open(annotoutfile, 'r') as f:
		for line in f:
			allannots.append(line.rstrip())

	allannots = list(allannots)
	allannots.sort()

	if request.method == 'POST':
		if request.form['submit'] == 'Draw Heatmap':
			heatmapobj = Heatmap()
			text = request.form['text']
			if not text:
				db_session.close()
				flash('No genes listed.  Please enter a list of gene names.')
				return render_template("genelist.html", annots=allannots)

			genelist = parseText(text)

			if len(genelist) == 0:
				db_session.close()
				flash('No genes listed.  Please enter a list of gene names.')
				return render_template("genelist.html", annots=allannots)

			# Get checkbox info and look up conditions
			annotlist = []
			for annot in allannots:
				if request.form.get(annot):
					annotlist.append(annot)

			if len(annotlist) == 0:
				db_session.close()
				flash('No condition types selected.  Please choose condition(s).')
				return render_template("genelist.html", annots=allannots)

			#  Limit search to first set of conditions results bc we only need the conditions through one gene to grab condition names
			adbgene = db_session.query(Gene).filter_by(descr=genelist[0], file_id=dbfile.id).first()
			dbconds = adbgene.get_conditions()
			condcnt = 0
			for c in dbconds:
				condcnt+=1
			condset = set([])
			for annot in annotlist:
				#condresults = Condition.query.whoosh_search(annot.lower(), limit=condcnt).all()
				condresults = db_session.query(Condition).filter(or_(Condition.annot1 == annot.lower(), Condition.annot2 == annot.lower(), Condition.annot3 == annot.lower())).all()
				for c in condresults:
					condset.add(c.condition)
			condlist = list(condset)

			#flash('condlist = ' + '\t'.join(condlist))
			#return render_template("genelist.html", annots=allannots)

			if(len(condlist) < 2):
				db_session.close()
				flash('Not enough conditions associated with '+annotlist[0])
				return render_template("genelist.html", annots=allannots)

			#  Make inputfile name
			fnstr = ''
			for i in range(0,len(annotlist)):
				annot = annotlist[i]
				annot = annot.replace(" ", "_").replace("#",'').replace(',','_').replace('\'','')
				fnstr+= annot+'_'

			inputfile = os.path.join(app.config['DATA_FOLDER'], (filename.rsplit('.', 1)[0]+'_'+fnstr+'.csv'))

			if not os.path.isfile(inputfile):
				#  Look up genes and conditions and output to file for makeHeatmap function
				OUT = open(inputfile, 'wb')
				header = 'Gene'
				for c in condlist:
					header+=','+c.split(':::')[1]
				OUT.write(header+'\n')
				newgenelist = []
				for gene in genelist:
					dbgene = db_session.query(Gene).filter(and_(Gene.descr==gene, Gene.file_id==dbfile.id)).first()
					if dbgene is None:
						continue
					else:
						newgenelist.append(gene)
					OUT.write(gene)
					dbconds = dbgene.get_conditions()
					for cond in condlist:
						dbcond = db_session.query(Condition).filter(and_(Condition.condition==cond,Condition.gene_id==dbgene.id)).first()
						OUT.write(','+dbcond.get_value())
					#for dbcond in dbconds:
					#	OUT.write(','+dbcond.get_value())
					OUT.write('\n')
				OUT.close()

			db_session.rollback()

			with open(inputfile, 'rb') as f:
				lines = f.readlines()
				num_lines = len([l for l in lines if l.strip(' \n') != '']) # Don't count black lines

			if num_lines == 1:
				flash('No data for this genelist')
				return render_template("genelist.html", annots=allannots)

			outputfiledata = os.path.join(app.config['DATA_FOLDER'], ('heatmapdata_'+fnstr+'.csv'))
			outputfilelab = os.path.join(app.config['DATA_FOLDER'], ('heatmaplab_'+fnstr+'.js'))

			if not os.path.isfile(outputfiledata) or not os.path.isfile(outputfilelab):
				heatmapobj.makeHeatmap(inputfile,outputfiledata,outputfilelab,app.config['DATA_FOLDER'],fnstr)
			#proc = ("R --no-save --args working_dir=", app.config['DATA_FOLDER'], " input_file=", os.path.basename(inputfile), " outputfilehc=", os.path.basename(outputfiledata), " outputfilelab=", os.path.basename(outputfilelab), 
			#	" username=", uname, " < /Users/mharris/Documents/work/bin/flask_stuff/mtbflask/R/HeatmapData.R")
			#p = subprocess.call("".join(proc), shell=True)
	        return redirect(url_for('.heatmap', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilelab))) #, pngrows=("hcrows_"+uname+".png"), pngcols=("hccols_"+uname+".png")))

	flash('This might take a minute.')
	return render_template("genelist.html", annots=allannots)

def getAllAnnots(filename):
	db_session = Session()
	allannots = set([])
	dbfile = db_session.query(File).filter_by(filename=filename).first()
	dbgenes = db_session.query(Gene).all()
	for gene in dbgenes:
		conditions = gene.get_conditions()
		for cond in conditions:
			annots = cond.get_annots()
			for annot in annots:
				if annot != 'na' and annot != '':
					allannots.add(annot)
		break # Just needed one gene to get all conditions and annotations

	db_session.rollback()

	outfile = os.path.join(app.config['DATA_FOLDER'], 'All_annots_'+dbfile.filename.rsplit('.')[0]+'.txt')
	OUT = open(outfile, 'wb')
	for annot in allannots:
		OUT.write(annot+'\n')
	OUT.close()
	#return allannots

@mod.route('/bicluster/<filename_trunc>/<bicluster>')
def bicluster(filename_trunc,bicluster):

	db_session = Session()

	#  Look for truncated file name in the files in DB and then look up this filename in DB
	dbfiles = db_session.query(File).all()
	filename = ''
	for f in dbfiles:
		if filename_trunc in f.filename:
			filename = f.filename
	dbfile = db_session.query(File).filter_by(filename=filename).first()
	
	#  Get the selected bicluster option and make filename for reading json
	bc = bicluster.replace('bicluster_','').lstrip('0') # Get just the number
	bcfname = os.path.join(app.config['DATA_FOLDER'],'biclusters', 'bc_'+bc+'.json')
	jsondata = codecs.open(bcfname, 'rU','utf-8')
	data = json.load(jsondata)
	genelist = data['genes']
	condlist = data['conditions']

	if(len(condlist) < 2):
		db_session.close()
		flash('Not enough conditions')
		return redirect(url_for('.displays', filename=filename))
	if(len(genelist) < 2):
		db_session.close()
		flash('Not enough genes for heatmap')
		return redirect(url_for('.displays', filename=filename))

	inputfile = os.path.join(app.config['DATA_FOLDER'], ('bc_'+bc+'.csv'))

	if not os.path.isfile(inputfile):

		#  Look up genes and conditions and output to file for makeHeatmap function
		OUT = open(inputfile, 'wb')
		header = 'Gene'
		for c in condlist:
			if ':::' in c: # Mtb data
				c = c.split(':::')[1]
			header+=','+c
		OUT.write(header+'\n')
		newgenelist = []
		for gene in genelist:
			dbgene = db_session.query(Gene).filter_by(descr=gene.lower()).filter_by(file_id=dbfile.id).first()
			if dbgene is None:
				continue
			else:
				newgenelist.append(gene)
			OUT.write(gene)
			for c in condlist:
				dbcond = db_session.query(Condition).filter_by(condition=c,gene_id=dbgene.id).first()
				if dbcond is None:
					OUT.write(',NA')
				else:
					OUT.write(','+dbcond.get_value())
			OUT.write('\n')
		OUT.close()

	db_session.rollback()

	with open(inputfile, 'rb') as f:
		lines = f.readlines()
		num_lines = len([l for l in lines if l.strip(' \n') != '']) # Don't count black lines

	if num_lines == 1:
		flash('No data for this bicluster.')
		return redirect(url_for('.displays', filename=filename))

	outputfiledata = os.path.join(app.config['DATA_FOLDER'], ('heatmapdata_'+bc+'.csv'))
	outputfilelab = os.path.join(app.config['DATA_FOLDER'], ('heatmaplab_'+bc+'.js'))

	if not os.path.isfile(outputfiledata) or not os.path.isfile(outputfilelab):
		heatmapobj = Heatmap()
		heatmapobj.makeHeatmap(inputfile,outputfiledata,outputfilelab,app.config['DATA_FOLDER'],bc)

	return redirect(url_for('.heatmap', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilelab)))

def parseText(sometext):
	sometext.rstrip()
	sometext = sometext.lower()
	alist = sometext.split('\r\n')
	return alist
"""
def makeStaticHeatmap():
    #fig = Figure()
    #axis = fig.add_subplot(1, 1, 1)

    cdict1 = {'red':   ((0.0, 0.0, 0.0),
    	(0.5, 0.0, 0.1),
    	(1.0, 1.0, 1.0)),
    'green': ((0.0, 0.0, 0.0),
    	(1.0, 0.0, 0.0)),
    'blue':  ((0.0, 0.0, 1.0),
    	(0.5, 0.1, 0.0),
    	(1.0, 0.0, 0.0))
    }
    blue_red1 = LinearSegmentedColormap('BlueRed1', cdict1)

    #canvas = FigureCanvas(fig)

    #  The data
    x = np.arange(0, np.pi, 0.1)
    y = np.arange(0, 2*np.pi, 0.1)
    X, Y = np.meshgrid(x,y)
    Z = np.cos(X) * np.sin(Y) * 10

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([1,2,3])
    fig.savefig(os.path.join(app.config['DATA_FOLDER'],'test.png'))

"""
 
