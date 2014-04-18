from flask import render_template, flash, redirect, session, url_for, request, g, make_response, send_from_directory
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
from app import app, db, oid, lm
from functools import wraps
import flask_openid
#from flask.ext.security.forms import LoginForm, ResetPasswordForm, RegisterForm, ForgotPasswordForm
#import flask.ext.security
#from flask.ext.security import login_required
#from flask.ext.security.recoverable import send_reset_password_instructions
#from forms import LoginForm
#from forms import SignupForm, SigninForm
from models import User, UserAdmin, File, Gene, Condition, ROLE_USER, ROLE_ADMIN
from forms import SearchForm, LoginForm


#from rpy2.robjects import r
#from rpy2.robjects import Formula
#from rpy2.robjects.packages import importr
#from rpy2 import robjects
import Heatmap
from Heatmap import *

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pylab as pl
import random
from cStringIO import StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import StringIO

#from pyvttbl import DataFrame # Pivot tables

import os
import json
import codecs # For opening JSON file from R
import subprocess
import csv
import operator





HEIGHT = WIDTH = 512



@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
        title = 'Home')

###  LOGIN FUNCTIONS  ###

@app.before_request
def before_request():
    g.user = current_user

@lm.user_loader
def load_user(uid):
    return User.query.get(int(uid))

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ['email','fullname'])
    return render_template('login.html', 
        title = 'Sign In',
        form = form,
        providers = app.config['OPENID_PROVIDERS'])#flask_openid.COMMON_PROVIDERS)

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        if resp.email.endswith('@{0}'.format(app.config['VALID_DOMAIN'])) or not app.config['VALID_DOMAIN']:
            user = User(email = resp.email, fullname=resp.fullname, role = ROLE_USER)
            db.session.add(user)
            db.session.commit()
        else:
            form = LoginForm()
            flash('Email does not contain a valid domain for login.')
            return render_template('login.html', 
                title = 'Sign In',
                form = form,
                providers = app.config['OPENID_PROVIDERS'])
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
	if not g.user:
		return redirect(url_for('login'))
	else:
		dbfiles = File.query.all()
		files=[]
		for f in dbfiles:
			files.append(f.filename)
		return render_template('profile.html', files=files)

###  FULL TEXT SEARCHING  ###

@app.route('/search', methods = ['POST'])
@login_required
def search():
	if request.method == 'POST':
		text = request.form['searchtext']
		return redirect(url_for('search_results', query = text))
	return redirect(url_for('profile'))

@app.route('/search_results/<query>')
@login_required
def search_results(query):
    generesults = Gene.query.whoosh_search(query.lower()).all() # All genes stored as lowercase
    condresults = set(Condition.query.whoosh_search(query.lower()).all()) # use set to remove duplicate elements
    condresults = list(condresults)
    expresults = File.query.whoosh_search(query).all()
    return render_template('search_results.html',
        query = query,
        generesults = generesults,
        condresults = condresults,
        expresults = expresults)

###  VISUALIZATIONS  ###

@app.route('/displays/<filename>', methods=['POST','GET'])
@login_required
def displays(filename):
    dbfile = File.query.filter_by(filename=filename).first()
    dbgenes = dbfile.get_genes()
    genelist = []
    for dbg in dbgenes:
        genelist.append(dbg.descr)
    biclusters = []
    for fname in os.listdir(os.path.join(app.config['DATA_FOLDER'],'biclusters')):
    	biclusters.append(os.path.basename(fname).rsplit('.')[0])
    if request.method == 'POST':
        if request.form['submit'] == 'Zoomplot':
            return redirect(url_for('zoomplot', genedescr=request.form['select1']))
        if request.form['submit'] == 'Lineplot':
            text = request.form['text']
            return redirect(url_for('d3lineplot',filename=filename, text=text))
        if request.form['submit'] == 'Heatmap':
            return redirect(url_for('genelist', filename=filename))
        if request.form['submit'] == 'Bicluster Heatmap':
        	return redirect(url_for('bicluster', filename=filename, bicluster=request.form['selectbc']))
    return render_template('displays.html', filename=filename, geneids=genelist, biclusters=biclusters)


@app.route('/zoomplot/<genedescr>')
@login_required
def zoomplot(genedescr):
	jsonfile = makeJSONdataZoomplot(genedescr)
	dbgene = Gene.query.filter_by(descr=genedescr).first()
	return render_template('d3zoomplot_conds.html', jsonobj=jsonfile, genename=genedescr)

@app.route('/d3lineplot/<filename>/<text>')
@login_required
def d3lineplot(filename, text):
    genelist = parseText(text)
    dbfile = File.query.filter_by(filename=filename).first()
    genedescrs = [x for x in genelist]
    jsonstr = '{'
    jsonstr = jsonstr+'\n\"labels\": '+json.dumps(genedescrs) + ','
    allvals = []
    ntimes = 0
    for g in genelist:
    	vals = [] # ea gene is going to have an array of values cooresponding to the conditions
    	dbgene = Gene.query.filter_by(descr=g, file_id=dbfile.id).first()
    	conds = dbgene.get_conditions()
    	for c in conds:
    		val = c.get_value()
    		vals.append(val)
    	ntimes = len(vals)
    	allvals.append(vals)
    jsonstr = jsonstr+'\n\"times\": ' + json.dumps([x for x in range(ntimes)])+','
    jsonstr = jsonstr+'\n\"curves\": '
    jsonstr=jsonstr+json.dumps(allvals)+'}'
    outfile = os.path.join(app.config['DATA_FOLDER'], 'json4lineplot_'+'test'+'_tmp.json')
    OUT = open(outfile, 'wb')
    OUT.write(jsonstr)
    return render_template('d3lineplot.html', jsonfile=os.path.basename(outfile))

###
#  Create JSON representation of data for a gene (used by zoomplot)
###
def makeJSONdataZoomplot(genedescr):
	genes = Gene.query.filter_by(descr=genedescr).all()

	for gene in genes:
		outputfilenm = gene.descr+'_json.txt'
		fulloutput = os.path.join(app.config['DATA_FOLDER'], outputfilenm)
		if (os.path.isfile(fulloutput)): #  Does file already exist?
			return outputfilenm

		conditions = gene.get_conditions()
		cond2vals = {}
		for cond in conditions:
			dbcond = Condition.query.filter_by(condition=cond).filter_by(gene_id=gene.get_id()).first() # all replicates
			condstr = dbcond.get_condition()
			val = dbcond.get_value()
			if val =='NA':
				continue
			cond2vals[condstr] = val

		with open(fulloutput, 'w') as f:
			f.write(unicode(json.dumps(cond2vals, ensure_ascii=False, indent=4, separators=(',', ': '))))
		f.close()
		#jsonobj = json.dumps(cond2vals, ensure_ascii=True)
		return outputfilenm

	#return jsonobj

###  HEATMAP FXNS  ###

@app.route('/heatmapinput/<filename>', methods=['GET','POST'])
@login_required
def heatmapinput(filename):
	dbfile = File.query.filter_by(filename=filename).first()

	#  Create big json file for d3

@app.route('/heatmap/<inputdata>/<inputlabels>') #'/<pngrows>/<pngcols>')
@login_required
def heatmap(inputdata, inputlabels): #, pngrows, pngcols):
	return render_template('d3heatmap.html', inputdata=inputdata, inputlabels=inputlabels) #, pngrows=pngrows, pngcols=pngcols)

@app.route('/genelist/<filename>', methods=['GET','POST'])
@login_required
def genelist(filename):
	#  Get user name from openid/email
	uname = g.user.email.split('@')[0]

	allannots = getAllAnnots(filename) #  Need only do this once...save to txt file when populating db?
	outputfiledata = os.path.join(app.config['DATA_FOLDER'], ('heatmapdata_'+str(uname)+'.csv'))
	outputfilelab = os.path.join(app.config['DATA_FOLDER'], ('heatmaphc_'+str(uname)+'.js'))
	inputfile = os.path.join(app.config['DATA_FOLDER'], (filename.rsplit('.', 1)[0]+'_'+str(uname)+'.csv'))
	dbfilename = os.path.join(app.config['DATA_FOLDER'], (filename.rsplit('.', 1)[0]+'.csv'))
	dbfile = File.query.filter_by(filename=os.path.basename(dbfilename)).first()
	if request.method == 'POST':
		if request.form['submit'] == 'Draw Heatmap':
			heatmapobj = Heatmap()
			text = request.form['text']
			if not text:
				flash('No genes listed.  Please enter a list of gene names.')
				return render_template("genelist.html", annots=allannots)

			genelist = parseText(text)

			if len(genelist) == 0:
				flash('No genes listed.  Please enter a list of gene names.')
				return render_template("genelist.html", annots=allannots)

			# Get checkbox info and look up conditions
			annotlist = []
			for annot in allannots:
				if request.form.get(annot):
					annotlist.append(annot)

			if len(annotlist) == 0:
				flash('No condition types selected.  Please choose condition(s).')
				return render_template("genelist.html", annots=allannots)

			numgenes = len(Gene.query.all())

			condset = set([])
			for annot in annotlist:
				#  Limit search to first numgenes results bc we only need the conditions through one gene to grab condition names
				condresults = Condition.query.whoosh_search(annot.lower(), limit=numgenes).all()
				for c in condresults:
					condset.add(c.condition)

			condlist = list(condset)

			if(len(condlist) < 2):
				flash('Not enough conditions associated with '+annotlist[0])
				return render_template("genelist.html", annots=allannots)

			#  Look up genes and conditions and output to file for makeHeatmap function
			OUT = open(inputfile, 'wb')
			print('opened output file for writing (input into heatmap fxn)')
			header = 'Gene'
			for c in condlist:
				header+=','+c.split(':::')[1]
			OUT.write(header+'\n')
			newgenelist = []
			for gene in genelist:
				dbgene = Gene.query.filter_by(descr=gene).filter_by(file_id=dbfile.id).first()
				if dbgene is None:
					continue
				else:
					newgenelist.append(gene)
				OUT.write(gene)
				#conds = dbgene.get_conditions()
				for c in condlist:
					dbcond = Condition.query.filter_by(condition=c,gene_id=dbgene.id).first()
					OUT.write(','+dbcond.get_value())
				OUT.write('\n')
			OUT.close()

			heatmapobj.makeHeatmap(inputfile,outputfiledata,outputfilelab,genelist,condlist,app.config['DATA_FOLDER'])
			#proc = ("R --no-save --args working_dir=", app.config['DATA_FOLDER'], " input_file=", os.path.basename(inputfile), " outputfilehc=", os.path.basename(outputfiledata), " outputfilelab=", os.path.basename(outputfilelab), 
			#	" username=", uname, " < /Users/mharris/Documents/work/bin/flask_stuff/mtbflask/R/HeatmapData.R")
			#p = subprocess.call("".join(proc), shell=True)
	        return redirect(url_for('heatmap', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilelab))) #, 
	        	#pngrows=("hcrows_"+uname+".png"), pngcols=("hccols_"+uname+".png")))
	flash('This might take a minute.')
	return render_template("genelist.html", annots=allannots)

def getAllAnnots(filename):
	allannots = set([])
	#user = User.query.filter_by(openid=g.user).first()
	#print(user)
	#uid = unicode(user.id)
	dbfile = File.query.filter_by(filename=filename).first()
	dbgenes = Gene.query.all()
	for gene in dbgenes:
		conditions = gene.get_conditions()
		for cond in conditions:
			annots = cond.get_annots()
			for annot in annots:
				if annot != 'na' and annot != '':
					allannots.add(annot)
		break # Just needed one gene to get all conditions and annotations
	return allannots

@app.route('/bicluster/<filename>/<bicluster>')
@login_required
def bicluster(filename,bicluster):
	uname = g.user.email.split('@')[0]
	dbfile = File.query.filter_by(filename=filename).first()
	outputfiledata = os.path.join(app.config['DATA_FOLDER'], ('heatmapdata_bc_'+str(uname)+'.csv'))
	outputfilelab = os.path.join(app.config['DATA_FOLDER'], ('heatmaphc_bc_'+str(uname)+'.js'))
	inputfile = os.path.join(app.config['DATA_FOLDER'], ('bicluster_'+str(uname)+'.csv'))

	#  Get the selected bicluster option and make filename for reading json
	bcfname = os.path.join(app.config['DATA_FOLDER'],'biclusters', bicluster+'.json')
	jsondata = codecs.open(bcfname, 'rU','utf-8')
	data = json.load(jsondata)
	genelist = data['genes']
	condlist = data['conditions']

	if(len(condlist) < 2):
		flash('Not enough conditions')
		return render_template("displays.html", filename=filename)
	if(len(genelist) < 2):
		flash('Not enough genes for heatmap')
		return render_template('displays.html', filename=filename)

	#  Look up genes and conditions and output to file for makeHeatmap function
	OUT = open(inputfile, 'wb')
	print('opened output file for writing (input into heatmap fxn)')
	header = 'Gene'
	for c in condlist:
		header+=','+c.split(':::')[1]
	OUT.write(header+'\n')
	newgenelist = []
	for gene in genelist:
		dbgene = Gene.query.filter_by(descr=gene.lower()).filter_by(file_id=dbfile.id).first()
		if dbgene is None:
			continue
		else:
			newgenelist.append(gene)
		OUT.write(gene)
		for c in condlist:
			dbcond = Condition.query.filter_by(condition=c,gene_id=dbgene.id).first()
			if dbcond is None:
				OUT.write(',NA')
			else:
				OUT.write(','+dbcond.get_value())
		OUT.write('\n')
	OUT.close()

	heatmapobj = Heatmap()
	heatmapobj.makeHeatmap(inputfile,outputfiledata,outputfilelab,genelist,condlist,app.config['DATA_FOLDER'])
	return redirect(url_for('heatmap', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilelab)))

def parseText(sometext):
	sometext.rstrip()
	sometext = sometext.lower()
	alist = sometext.split('\r\n')
	return alist

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
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
 
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response
"""
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route('/upload_file', methods=['GET','POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        file = request.files['file']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filedescr = filename.rsplit('.', 1)[1]

            expname = request.form['experimentname']
            location = app.config['DATA_FOLDER']

            #  Check if file already in db
            if (File.query.filter_by(filename=filename).filter_by( expname=expname).filter_by( location=location).count() > 0):
                flash('File already exists.')
                return redirect(url_for('profile'))
            file.save(os.path.join(location, filename)) 
            dbfile = File(filename=filename, location=location, filedescr=filedescr, expname=expname, loaded=False)

            #  If csv check if field names are correct, if not do not save to db
            if filedescr == 'csv':
                c = checkCsvFormat(filename)
                if c == False:
                    flash('Comma separated file does not have correct headers.  Please see instructions.')
                    return render_template('upload.html')

            db.session.add(dbfile)
            db.session.commit()

            ext = filename.rsplit('.', 1)[1]
            if ext == 'RData':
                processRdata(filename)
                dbfile.loaded = True
                db.session.commit() #  Commit the loaded==True setting
            return redirect(url_for('profile'))
    flash('Uploading and processing file.  This might take a minute, please do not reload...')
    return render_template('upload.html')


#  Run an R script to read an Rdata file - mtu_inf_111813.csv

def processRdata(filename):

	#  Get experiment name from RData file
	dbfile = File.query.filter_by(filename=filename).first()
	exp = dbfile.expname

	outputfile = filename.rsplit('.', 1)[0] + '.csv'

	#  Does this file already exist?
	location = app.config['DATA_FOLDER']
	if (File.query.filter_by(filename=outputfile).filter_by( location=location).count() > 0):
		flash('File already exists.')
		return 0

	proc = ("R --no-save --args working_dir=", app.config['DATA_FOLDER'], " rdata_file=", filename, " outputfile=", outputfile, " < /Users/mharris/Documents/work/bin/R_scripts/ProcessRdata.R")
	p = subprocess.Popen("".join(proc), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	f = File(filename=outputfile, location=location, filedescr='csv', loaded=True, expname=exp)
	db.session.add(f)
	db.session.commit()

	#  Parse RData file to get genes and conditions (adding them to DB as well:  user -> file -> genes -> conditions -> values)
	parseRatiosFile(os.path.join(app.config['DATA_FOLDER'],outputfile),os.path.join(app.config['DATA_FOLDER'],"20140204_Mtb_condsubsets_unix.csv"))

	return 0

# For mtu_inf_111813.RData

def parseRatiosFile(ratiosfile,annotfile):

	location = app.config['DATA_FOLDER']
	dbfile = File()
	basenm = os.path.basename(ratiosfile)
	print(basenm)
	dbfile = File.query.filter_by(filename=basenm).filter_by( location=location).first() # This file should already exist, made in processRdata

	#  Parse annotations file (for Mtb - from Eliza)
	condsub2annot = {}
	condsub22annot = {}
	condsub32annot = {}
	with open(annotfile, 'rb') as f:
		for line in csv.DictReader(f, delimiter=','):
			if line['condition.subset']:
				condsub = line['condition.subset']
			else:
				condsub = ""
			if line['condition.subset2']:
				condsub2 = line['condition.subset2']
			else:
				condsub2 = ""
			if line['condition.subset3']:
				condsub3 = line['condition.subset3']
			else:
				condsub3 = ""
			
			sample = line['sample']
			expid = line['experimentID']
			pmid = line['PMID']
			strain = line['strain']

			condition = str(expid)+':::'+sample
			condsub2annot[condition] = condsub
			condsub22annot[condition] = condsub2
			condsub32annot[condition] = condsub3

	lncnt = 0
	with open(ratiosfile, 'rb') as file:
		print('opened ratiosfile for reading.')
		lines = file.readlines()
		
		conditions = []
		for line in lines:
			line.rstrip()
			linespl = line.split(',')
			if lncnt == 0:
				for i in range(2, len(linespl)):
					condition = linespl[i]
					conditions.append(condition)
				lncnt+=1
				continue

			gene = linespl[1].lower()
			#dbgene = Gene.query.filter_by(descr=gene,file_id=dbfile.get_id()).first()
			#dbgeneid = dbgene.get_id()

			dbgene = Gene(descr=gene,file_id=dbfile.id)
			db.session.add(dbgene)
			print('added gene '+gene)
			db.session.commit()

			for i in range(0,len(conditions)):
				ratio = linespl[i+2]
				condition = conditions[i]

				annot1 = 'na'
				annot2 = 'na'
				annot3 = 'na'

				#  Look up annotations
				if condition in condsub2annot:
					annot1 = condsub2annot[condition].lower()
				if condition in condsub22annot:
					annot2 = condsub22annot[condition].lower()
				if condition in condsub32annot:
					annot3 = condsub32annot[condition].lower()
					print(annot3)

				s = condition.split('.')
				rep = s[len(s)-1] # Get everything after last '.'
				dbcond = Condition(condition=condition,value=ratio, gene_id=dbgene.id, replicate=rep, annot1=annot1, annot2=annot2, annot3=annot3)
				print(dbcond)
				db.session.add(dbcond)
				print('added condition '+ condition)

			lncnt+=1

			if lncnt > 10: break # For testing only first 10 genes

	print('committing session.')
	db.session.commit()
	print('session committed.')

	return 0
			
def checkCsvFormat(filename):
	fullfilename = os.path.join(app.config['DATA_FOLDER'],filename)
	with open(fullfilename, 'rb') as f:
		reader = csv.DictReader(f, delimiter=',')
		fnames = reader.fieldnames
		if 'name' in fnames and 'replicate' in fnames and 'data' in fnames and 'condition' in fnames:
			print('field names correct')
			return True
		else:
			print('field names incorrect')
			return False

def parseCSVFile(filename):
	user = User.query.filter_by(email = session['email']).first()
	uid = user.get_id()
	dbfile = File.query.filter_by(filename=filename).filter_by(user_id=uid).filter_by(location=app.config['DATA_FOLDER']).first()

	#  Read in data and commit to db
	fullfilename = os.path.join(app.config['DATA_FOLDER'],filename)
	with open(fullfilename, 'rb') as f:
		for line in csv.DictReader(f, delimiter=','):
			name = line['name']
			replicate = line['replicate']
			condition = line['condition']
			data = line['data']
			location = app.config['DATA_FOLDER']
			dbgene = Gene.query.filter_by(descr=name).filter_by(file_id=dbfile.get_id()).first()
			if not dbgene:
				dbgene = Gene(descr=name,file_id=dbfile.get_id())
				db.session.add(dbgene)
				db.session.commit()
			dbcond = Condition.query.filter_by(condition=condition,value=data, gene_id=dbgene.get_id(), replicate=replicate).first()
			if not dbcond:
				dbcond = Condition(condition=condition,value=data, gene_id=dbgene.get_id(), replicate=replicate)
				db.session.add(dbcond)
				db.session.commit()
	#db.session.commit()
	f.close()

	#  Now can set loaded to true
	dbfile.set_loaded()


@app.route('/pivot_boxplot/<filename>', methods=['GET'])
def pivot_boxplot(filename):
	uid = User.query.filter_by(email = session['email']).first().get_id()
	factors = ['name','condition']
	outputfn = pivotTableBoxplot(filename,uid,factors)
	return render_template('images.html', image=os.path.basename(outputfn))

def makeBoxplotFile(ratiosfile, genenm):
    print('opened file for writing')

    #  Test dict for jsonifying
    geneDict = {}
    testDict = {}
    cond2ratios = {}

    with open(ratiosfile, 'rb') as file:
    	lncnt = 1
    	conditions = []
    	lines = file.readlines()
    	for line in lines:
			line.rstrip()
			linespl = line.split(",")
			if lncnt == 1:
				for i in range(2,len(linespl)):
					condition = linespl[i]
					condition = condition[7:-1]
					conditions.append(condition)
				lncnt = 2
				continue
	
			gene = linespl[1] #  Second field is gene name, first is index

			if gene != genenm:
				continue

			cond2ratio = {}

			if gene in geneDict:
				cond2ratio = geneDict[gene]
			else:
				geneDict[gene] = {}

			for i in range(0,len(conditions)):
				ratio = linespl[i+2]
				if 'NA' in ratio:
					ratio = 0
				condition = conditions[i]
				#OUT.write(condition+','+gene+','+ratio+'\n')

				if condition in cond2ratio:
				    ratios = cond2ratio[condition]
				    ratios.append(ratio)
				    cond2ratio[condition] = ratios
				    cond2ratios[condition] = ratios
				else:
				    ratios = []
				    ratios.append(ratio)
				    cond2ratio[condition] = ratios
				    cond2ratios[condition] = ratios

				geneDict[gene] = cond2ratio

    #OUT.close()

    print('done parsing ratios file')

    #  Output the dict as json object
    with open(os.path.join(app.config['DATA_FOLDER'], 'jsondata.txt'), 'w') as f:
    	f.write(unicode(json.dumps(cond2ratios, ensure_ascii=False, indent=4, separators=(',', ': '))))

    print('done printing json file')


# Test plotting

@app.route('/plot.png')
def plot():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
 
    xs = range(100)
    ys = [random.randint(1, 50) for x in xs]
 
    axis.plot(xs, ys)
    canvas = FigureCanvas(fig)
    output = StringIO.StringIO()
    canvas.print_png(output)
    response = make_response(output.getvalue())
    response.mimetype = 'image/png'
    return response

# Testing D3

@app.route('/d3zoomplot')
def d3zoomplot():
	return render_template("d3zoomplot_conds.html")

#  Test loading json

@app.route('/loadjson')
def loadjson():
	return render_template("readjson.html")



@app.route('/svg_example')
def svg_example():
	return render_template('cluster0518.html')


@app.route('/data')
@app.route('/data/<int:ndata>')
def data(ndata=100):
	x = 10 * np.random.rand(ndata) - 5
	y = 0.5 * x + 0.5 * np.random.randn(ndata)
	A = 10. ** np.random.rand(ndata)
	c = np.random.rand(ndata)
	return json.dumps([{"_id": i, "x": x[i], "y": y[i], "area": A[i], "color": c[i]} for i in range(ndata)])

@app.route('/rpy2_hist')
def some_rpy2():
	flash('Loading data...please wait')
	r.load('mtu_inf_111813.RData')
	pm = r['predictor.mats']
	pmm = pm.rx(1)
	dataframe = r['data.frame']
	df = dataframe(pmm)
	firstcol = df.rx(1)
	seccol = df.rx(2)

	lattice = importr('lattice')
	xyplot = lattice.xyplot
	rprint = robjects.globalenv.get("print")

	#formula = Formula('firstcol ~ seccol')
	#formula.getenvironment()['firstcol'] = df.rx2(1)
	#formula.getenvironment()['seccol'] = df.rx2(2)
	#p = lattice.xyplot(formula)

	grdevices = importr('grDevices')

	#filenm = app.config['IMGS_FOLDER'] + 'hist.png'
	filenm = 'hist.png' # why is this in tmp still???

	grdevices.png(file=filenm, width=512, height=512)
	p = r.histogram(df.rx2(1))
	rprint(p) # works
	grdevices.dev_off()

	return render_template("hist.html", image='static/tmp/hist.png')


"""