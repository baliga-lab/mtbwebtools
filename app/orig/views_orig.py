from flask import render_template, flash, redirect, session, url_for, request, g, make_response, send_from_directory
from flask.ext.login import login_user, logout_user, current_user
from werkzeug import secure_filename
from app import app, db, login_manager, openid
from functools import wraps
#from flask.ext.security.forms import LoginForm, ResetPasswordForm, RegisterForm, ForgotPasswordForm
#import flask.ext.security
#from flask.ext.security import login_required
#from flask.ext.security.recoverable import send_reset_password_instructions
#from forms import LoginForm
#from forms import SignupForm, SigninForm
from models import User, UserAdmin, File, Gene, Condition
from forms import SearchForm


from rpy2.robjects import r
from rpy2.robjects import Formula
from rpy2.robjects.packages import importr
from rpy2 import robjects

import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
#import pylab as pl
import random
#from cStringIO import StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import StringIO

from pyvttbl import DataFrame # Pivot tables

import os
import json
import subprocess
import csv
import operator

import Heatmap
from Heatmap import *



HEIGHT = WIDTH = 512

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if g.user is None:
			return redirect(url_for('login', next=request.url))
		return f(*args, **kwargs)
	return decorated_function

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
        title = 'Home')


"""
@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()


@app.after_request
def after_request(response):
    db_session.remove()
    return response

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    #Does the login via OpenID.  Has to call into `oid.try_login`
    #to start the OpenID machinery.
    
    # if we are already logged in, go back to were we came from
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            pape_req = pape.Request([])
            return oid.try_login(openid, ask_for=['email', 'nickname'],
                                         ask_for_optional=['fullname'],
                                         extensions=[pape_req])
    return render_template('login_oid.html', next=oid.get_next_url()
                           )


@oid.after_login
def create_or_login(resp):
    #This is called when login with OpenID succeeded and it's not
    #necessary to figure out if this is the users's first login or not.
    #This function has to redirect otherwise the user will be presented
    #with a terrible URL which we certainly don't want.
    
    session['openid'] = resp.identity_url
    if 'pape' in resp.extensions:
        pape_resp = resp.extensions['pape']
        session['auth_time'] = pape_resp.auth_time
    user = User.query.filter_by(openid=resp.identity_url).first()
    email = user.email
    if not email.endswith('@{0}'.format('systemsbiologytest')):
    	flash('Not a valid email')
    	return redirect(url_for('login'))
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    #If this is the user's first login, the create_or_login function
    #will redirect here so that the user can set up his profile.
    
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db_session.add(User(name, email, session['openid']))
            db_session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())


@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    #Updates a profile
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db_session.delete(g.user)
            db_session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('index'))
        form['name'] = request.form['name']
        form['email'] = request.form['email']
        if not form['name']:
            flash(u'Error: you have to provide a name')
        elif '@' not in form['email']:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.user.name = form['name']
            g.user.email = form['email']
            db_session.commit()
            return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)


@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())

@login_manager.user_loader
def load_user(uid):
	return db.session.query(User).get(uid)
	"""

"""
@app.route('/signup', methods=['GET', 'POST'])
def signup():
	form = RegisterForm()
	return render_template('security/register_user.html', register_user_form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    #user = User()
    if form.validate_on_submit():
        # login and validate the user...
        login_user(form.user, remember=form.remember.data)
        session['email'] = request.form['email']
        flash("Logged in successfully.")
        return redirect(request.args.get("next") or url_for('profile'))
    return render_template('security/login_user.html', login_user_form=form)


@app.route('/logout')
#@login_required
def logout():
	session.pop('email', None)
	logout_user()
	return redirect(url_for('login'))

#  Not working
@app.route('/forgot_password', methods=['POST','GET'])
def forgot_password():
    form = ForgotPasswordForm()
    if request.method == 'POST':
        if form.validate_on_submit():
        	user = User.query.filter_by(email=form.email.data).first()
        	send_reset_password_instructions(form.user)
        	return redirect(url_for('reset_password'))
    return render_template('security/forgot_password.html', forgot_password_form=form)

#  Not working
@app.route('/reset_password', methods=['GET','POST'])
def reset_password():
	form = ResetPasswordForm()
	#if request.method == 'POST':
	#	if form.validate_on_submit():
	#		user = User.query.filter_by(email=session['email']).first()
	#		user.token = randint(0, sys.maxint)
	#		db.session.commit()
	#		body = render_template("Reset password.", recipient=user)
	#		mail.send_message(subject="Password Reset" + ": Reset your password", recipients=[user.email], body=body)
	#		flash("Your password has been reset, check your email.", "success")
	#		return redirect(url_for('profile'))
	return render_template('security/reset_password.html', reset_password_form=form)
"""
@app.route('/profile')
@login_required
def profile():
	if not session['openid']:
		return redirect(url_for('login'))
	else:
		dbfiles = File.query.all()
		files=[]
		for f in dbfiles:
			files.append(f.filename)
		return render_template('profile.html', files=files)


#@app.route('/signin', methods=['GET', 'POST'])
#def signin():
#	form = SigninForm()
#	if request.method == 'POST':
#		if form.validate() == False:
#			return render_template('signin.html', form=form)
#		else:
#			session['email'] = form.email.data
#			return redirect(url_for('profile'))
#	elif request.method == 'GET':
#		return render_template('signin.html', form=form)

#@app.route('/signout')
#def signout():
#	if 'email' not in session:
#		return redirect(url_for('signin'))
#	session.pop('email', None)
#	return redirect(url_for('index'))


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

###  GENE ACTIONS  ###

@app.route('/genepage/<geneid>')
@login_required
def genepage(geneid):
	dbgene = Gene.query.filter_by(id=geneid).first()
	return redirect(url_for('displaysgene', geneid=geneid))

@app.route('/displaysgene/<geneid>', methods=['GET','POST'])
@login_required
def displaysgene(geneid):
	if request.method == 'POST':
		if request.form['submit'] == 'Boxplot':
			return redirect(url_for('testjsonpassing', geneid=geneid))
		if request.form['submit'] == 'Scatterplot':
			return redirect(url_for('zoomplot', geneid=geneid))
		return render_template('display_choices.html')
	return render_template('display_choices.html')

@app.route('/exppage/<filename>')
@login_required
def exppage(filename):
	dbfile = File.query.filter_by(filename=filename).first()
	return redirect(url_for('displayexp', filename=dbfile.filename))

@app.route('/displayexp/<filename>', methods=['GET','POST'])
@login_required
def displayexp(filename):
	if request.method == 'POST':
		if request.form['submit'] == 'Heatmap':
			return redirect(url_for('genelist', filename=filename))
	return render_template('displayexp.html', filenm=filename)

@app.route('/zoomplot/<geneid>')
@login_required
def zoomplot(geneid):
	jsonfile = makeJSONdata(geneid)
	dbgene = Gene.query.filter_by(id=geneid).first()
	return render_template('d3zoomplot_conds.html', jsonobj=jsonfile, genename=dbgene.descr)

###
#  Create JSON representation of data for a gene (used by zoomplot)
###
def makeJSONdata(geneid):
	user = User.query.filter_by(email=session['email']).first()
	uid = user.get_id()
	genes = Gene.query.filter_by(id=geneid).all()

	for gene in genes:
		outputfilenm = gene.descr+'_json.txt'
		fulloutput = os.path.join(app.config['DATA_FOLDER'], outputfilenm)
		if (os.path.isfile(fulloutput)): #  Does file already exist?
			return outputfilenm

		conditions = gene.get_conditions()
		cond2vals = {}
		for cond in conditions:
			print(cond)
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


###  FILE UPLOADING  ###

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

###  TOOL BUTTONS  ###

@app.route('/tools/<filename>', methods=['GET','POST'])
@login_required
def tools(filename):
	dbfile = File.query.filter_by(filename=filename).filter_by( location=app.config['DATA_FOLDER']).first() # Added and commited to db in upload fxn
	if request.method == 'POST':
		if request.form['submit'] == 'Load':
			if dbfile.is_loaded(): #  File already processed
			    flash('File already loaded and committed to database.')
			    return render_template('tools.html', filenm=filename, otherbuttons=True)
			if ext == 'RData':
				processRdata(filename) # Convert to ratios file, save genes and conditions to db, this takes some time
				dbfile.set_loaded()
				dbfile.loaded = True
				db.session.commit() #  Commit the loaded==True setting
				return render_template('tools.html', filenm=filename, otherbuttons=True)
			if ext == 'csv' or ext == 'CSV':
				parseCSVFile(filename) # Save the csv file input to db
				dbfile.set_loaded()
				dbfile.loaded = True
				db.session.commit()
				return render_template('tools.html', filenm=filename, otherbuttons=True)
			return render_template('tools.html', filenm=filename, otherbuttons=True)
		if request.form['submit'] == 'Heatmap':
			return redirect(url_for('genelist', filename=filename))
		if request.form['submit'] == 'Export':
			return render_template('tools.html', filenm=filename, otherbuttons=True)
	flash('This might take a minute, please do not reload...')
	if dbfile.is_loaded():
		flash("File already loaded.")
		return render_template('tools.html', filenm=filename, otherbuttons=True)
	else:
		return render_template('tools.html', filenm=filename, otherbuttons=False)


###  HEATMAP FXNS  ###

@app.route('/heatmap/<inputdata>/<inputlabels>', methods=['GET','POST'])
@login_required
def heatmap(inputdata, inputlabels):#,inputdata,inputlabels):
	return render_template('d3heatmap_select.html', inputdata=inputdata, inputlabels=inputlabels)#, inputlabels=inputlabels)

@app.route('/genelist/<filename>', methods=['GET','POST'])
@login_required
def genelist(filename): # filename is the RData file
	allannots = getAllAnnots(filename)
	user = User.query.filter_by(email=session['email']).first()
	uid = user.get_id()
	outputfiledata = os.path.join(app.config['DATA_FOLDER'], ('heatmapdata_'+str(uid)+'.csv'))
	outputfilehc = os.path.join(app.config['DATA_FOLDER'], ('heatmaphc_'+str(uid)+'.js'))
	inputfile = os.path.join(app.config['DATA_FOLDER'], (filename.rsplit('.', 1)[0]+'_tmp.csv'))
	dbfilename = os.path.join(app.config['DATA_FOLDER'], (filename.rsplit('.', 1)[0]+'.csv'))
	dbfile = File.query.filter_by(filename=os.path.basename(dbfilename),user_id=uid).first()
	print(dbfile)
	if request.method == 'POST':
		print('in post method')
		if request.form['submit'] == 'Draw Heatmap':
			heatmapobj = Heatmap()
			text = request.form['text']
			print('got text')
			genelist = parseText(text)

		#	# Get checkbox info and look up conditions
			annotlist = []
			for annot in allannots:
				if request.form.get(annot):
					annotlist.append(annot)
			condset = set([])
			for annot in annotlist:
				condresults = Condition.query.whoosh_search(annot.lower()).all() # Get list of unicode conditions
				for cond in condresults:
					condobjs = Condition.query.filter_by(condition=cond).all() # Get Condition objects associated with unicode conditions
					for c in condobjs:
						condname = c.get_condition() # Get the condition name from Condition object
						condset.add(condname) #  Ad to set of unicode conditions (all associated with annotations)

			condlist = list(condset) #  Convert to set for iterating over
			if(len(condlist) < 2):
				flash('Not enough conditions associated with '+annotlist[0])
				return render_template("genelist.html", annots=allannots)

			#  Look up genes and conditions and output to file for makeHeatmap function
			OUT = open(inputfile, 'wb')
			print('opened output file for writing (input into heatmap fxn)')
			header = 'Gene'
			for c in condlist:
				header+=','+c
			OUT.write(header+'\n')
			for gene in genelist:
				dbgene = Gene.query.filter_by(descr=gene).filter_by(file_id=dbfile.id).first()
				print(dbgene)
				OUT.write(gene)
				#conds = dbgene.get_conditions()
				for c in condlist:
					dbcond = Condition.query.filter_by(condition=c,gene_id=dbgene.id).first()
					OUT.write(','+dbcond.get_value())
				OUT.write('\n')
			OUT.close()

			heatmapobj.makeHeatmap(inputfile,outputfiledata,outputfilehc,genelist,condlist)
			print('made heatmap, rendering tempate')
			#response = make_response(render_template('d3heatmap_select.html', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilehc)))
			#response.headers.add('Cache-Control', 'no-cache, no-store')
			#response.headers.add('Pragma', 'no-cache')
	        #return render_template('d3heatmap_select.html', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilehc))
	        return redirect(url_for('heatmap', inputdata=os.path.basename(outputfiledata), inputlabels=os.path.basename(outputfilehc)))
	return render_template("genelist.html", annots=allannots)

def getAllAnnots(filename):
	allannots = set([])
	user = User.query.filter_by(email=session['email']).first()
	uid = user.get_id()
	dbfile = File.query.filter_by(filename=filename, user_id=uid).first()
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

def parseText(sometext):
	sometext.rstrip()
	alist = sometext.split('\r\n')
	print(alist)
	return alist

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

				annot1 = ""
				annot2 = ""
				annot3 = ""

				#  Look up annotations
				if condition in condsub2annot:
					annot1 = condsub2annot[condition].lower()
				print(annot1)
				if condition in condsub22annot:
					annot2 = condsub22annot[condition].lower()
				if condition in condsub32annot:
					annot3 = condsub32annot[condition].lower()

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




@app.route('/jsonfile')
def jsonfile():
	return render_template('d3boxplot_file.html')

def pivotTableBoxplot(filename,uid,factors):
	df = DataFrame()
	df.read_tbl(os.path.join(app.config['DATA_FOLDER'], filename))
	df.box_plot('data',factors)
	origoutputfn = "box(data~"+factors[0]
	for i in range(1,len(factors)):
		origoutputfn+=("_X_"+factors[i])
	origoutputfn+=").png"
	outputfn = 'box_plot'
	for i in range(0,len(factors)):
		outputfn+='_'+factors[i]
	outputfn+='.png'

	#  TODO:  check if file exists

	#  Need to move/rename because output automatically goes to the base directory
	os.rename(os.path.join(app.config['BASEDIR'], origoutputfn), os.path.join(app.config['DATA_FOLDER'], outputfn))
	return outputfn




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
