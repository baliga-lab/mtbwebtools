import sys, numpy, scipy, os
#os.environ['MPLCONFIGDIR'] = '/tmp/'
#import matplotlib
#matplotlib.use('Agg')
import scipy.cluster.hierarchy as hier
import scipy.spatial.distance as dist
#import matplotlib.pyplot as plt
#import pylab as pl

class Heatmap:

	def makeHeatmap(self,inputfile,outputfiledata,outputfilelab,datafolder,filestr):
		#import the data into a native 2d python array
		inFile = open(inputfile,'r')
		colHeaders = inFile.next().strip().split(',')[1:]

		rowHeaders = []
		dataMatrix = []
		cnt = 0
		for line in inFile:
			data = line.strip().split(',')
			rowHeaders.append(data[0])
			dataMatrix.append([float(x) if x != 'NA' else numpy.nan for x in data[1:]])

		### ORDER GENES ###

		#convert native python array into a numpy array
		dataMatrix = numpy.array(dataMatrix)

		#calculate distance matrix
		distanceMatrix = dist.pdist(dataMatrix, 'chebyshev')
		distanceSquareMatrix = dist.squareform(distanceMatrix)

		#calculate linkage matrix
		linkageMatrix = hier.linkage(distanceSquareMatrix, method='complete')
		cutoff = 0.5*max(linkageMatrix[:,2])
		#linkageMatrix = hier.linkage(distanceMatrix)

		#get the order of the dendrogram leaves
		try:
			heatmapOrder = hier.leaves_list(linkageMatrix)
		except ValueError:
			OUT1 = open(outputfiledata,'wb')
			OUT1.write('row_idx,col_idx,log2ratio')
			OUT1.close()
			OUT2 = open(outputfilelab,'wb')
			OUT2.write('var hcrow = [];\n')
			OUT2.write('var hccol = [];\n')
			OUT2.write('var rowLabel = [];\n')
			OUT2.write('var colLabel = [];\n')
			OUT2.close()
			return 1


		#reorder the data matrix and row headers according to leaves
		orderedDataMatrix = dataMatrix[heatmapOrder,:]
		rowHeaders = numpy.array(rowHeaders)
		orderedRowHeaders = rowHeaders[heatmapOrder,:]

		### ORDER CONDITIONS ###

		dataMatrixT = [[ dataMatrix[row][col] for row in range(0,len(dataMatrix)) ] for col in range(0,len(dataMatrix[0])) ] # Transpose

		dataMatrixT = numpy.array(dataMatrixT)

		#calculate distance matrix and convert to squareform
		distanceMatrixT = dist.pdist(dataMatrixT, 'chebyshev')
		distanceSquareMatrixT = dist.squareform(distanceMatrixT)


		#calculate linkage matrix
		linkageMatrixT = hier.linkage(distanceSquareMatrixT, method='complete')
		cutoffT = 0.5*max(linkageMatrixT[:,2])
		#linkageMatrixT = hier.linkage(distanceMatrixT)

		#get the order of the dendrogram leaves
		try:
			heatmapOrderT = hier.leaves_list(linkageMatrixT)
		except ValueError:
			OUT1 = open(outputfiledata,'wb')
			OUT1.write('row_idx,col_idx,log2ratio')
			OUT1.close()
			OUT2 = open(outputfilelab,'wb')
			OUT2.write('var hcrow = [];\n')
			OUT2.write('var hccol = [];\n')
			OUT2.write('var rowLabel = [];\n')
			OUT2.write('var colLabel = [];\n')
			OUT2.close()
			return 1

		#reorder the data matrix and col (Conditions) headers according to leaves
		orderedDataMatrixT = dataMatrixT[heatmapOrderT,:]
		colHeaders = numpy.array(colHeaders)
		orderedColHeaders = colHeaders[heatmapOrderT,:]

		"""
		#  Output to csv file
		OUT1 = open(outputfiledata,'wb')
		OUT1.write('row_idx,col_idx,log2ratio')
		matrixOutput = []
		row = 1
		for rowData in orderedDataMatrix:
			col = 1
			rowOutput = []
			for colData in rowData:
				OUT1.write('\n'+str(row)+','+str(col)+','+str(colData))
				col += 1
			row += 1
		OUT1.close()
		"""

		#  Output to csv file (rows are conditions, cols are genes)
		OUT1 = open(outputfiledata,'wb')
		OUT1.write('row_idx,col_idx,log2ratio')
		row = 1
		for rowData in dataMatrixT:
			col = 1
			for colData in rowData:
				OUT1.write('\n'+str(row)+','+str(col)+','+str(colData))
				col += 1
			row += 1
		OUT1.close()

		OUT2 = open(outputfilelab,'wb')
		OUT2.write('var hcrow = ' + str([x+1 for x in heatmapOrderT]) + ";"+"\n")
		OUT2.write('var hccol = ' + str([x+1 for x in heatmapOrder]) + ";"+"\n")
		OUT2.write('var rowLabel = ' + str([x for x in colHeaders]) + ";"+"\n")
		OUT2.write('var colLabel = ' + str([x for x in rowHeaders]) + ";"+"\n")
		OUT2.close()

		return 0
"""
		#  Plot the dendrograms!

		#  Gene dendrogram

		plt.subplot(1,1,1)

		hier.dendrogram(linkageMatrix,
			color_threshold=cutoff,
			truncate_mode='lastp',
			labels=rowHeaders,
			show_leaf_counts=False
			)

		fig = plt.gcf()
		fig.set_size_inches(18,8)
		#plt.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
		plt.savefig(os.path.join(datafolder,'hc_genes'+filestr+'.png'))

		#  Conditions dendrogram

		plt.clf()

		plt.subplot(1,1,1)

		print(colHeaders)

		hier.dendrogram(linkageMatrixT,
			color_threshold=cutoffT,
			orientation='right',
			labels=colHeaders,
			show_leaf_counts=False
			)

		fig = plt.gcf()
		fig.set_size_inches(18,0.5*len(colHeaders))
		#plt.subplots_adjust(left=0.0, right=2.0, bottom=0.0, top=1.0)
		plt.savefig(os.path.join(datafolder,'hc_conds'+filestr+'.png'))
"""
		