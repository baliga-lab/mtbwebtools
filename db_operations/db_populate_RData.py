from app import app, db
from app.models import File, Condition, Gene
import os
import optparse
import subprocess
import csv

def processRdata(filename, annotfile, outputfile):

	#  Get experiment name from RData file
	#dbfile = File.query.filter_by(filename=filename).first()
	#exp = dbfile.expname

	#outputfile = filename.rsplit('.', 1)[0] + '.csv'

	#  Does this file already exist?
	location = app.config['DATA_FOLDER']
	if (File.query.filter_by(filename=outputfile).filter_by( location=location).count() > 0):
		print('File already exists.')
	else:
		proc = ("/tools/bin/R --no-save --args working_dir=", app.config['DATA_FOLDER'], " rdata_file=", filename, " outputfile=", outputfile, " < R/ProcessRdata.R")
		p = subprocess.call("".join(proc), shell=True)#, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		f = File(filename=outputfile, location=location, filedescr='ratios', loaded=True)
		db.session.add(f)
		db.session.commit()

	#  Parse RData file to get genes and conditions (adding them to DB as well:  user -> file -> genes -> conditions -> values)
	parseRatiosFile(os.path.join(app.config['DATA_FOLDER'],outputfile),os.path.join(app.config['DATA_FOLDER'],annotfile))

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
					annot1 = condsub2annot[condition].rstrip().lower()
				if condition in condsub22annot:
					annot2 = condsub22annot[condition].rstrip().lower()
				if condition in condsub32annot:
					annot3 = condsub32annot[condition].rstrip().lower()

				s = condition.split('.')
				rep = s[len(s)-1] # Get everything after last '.'
				dbcond = Condition(condition=condition,value=ratio, gene_id=dbgene.id, replicate=rep, annot1=annot1, annot2=annot2, annot3=annot3)
				#print(dbcond)
				db.session.add(dbcond)
				#print('added condition '+ condition)

			#lncnt+=1

			#if lncnt > 10: break # For testing only first 10 genes

	print('committing session.')
	db.session.commit()
	print('session committed.')

	return 0

def main():

	#  Get and parse options from command line
	op = optparse.OptionParser()
	op.add_option('-i', '--input_file', help='The RData cMonkey/inferelator output')
	op.add_option('-a', '--annot_file', help='The condition annotation file (in unix format)')
	op.add_option('-o', '--output_file', help='The output file name')
	opt, args = op.parse_args()
	if not opt.input_file:
		op.error('need --input_file option')
	if not opt.annot_file:
		op.error('need --annot_file option')
	if not opt.output_file:
		op.error('need --output_file option')

	processRdata(opt.input_file,opt.annot_file,opt.output_file)


if __name__ == '__main__':
	main()
