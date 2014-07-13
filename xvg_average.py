#generic python modules
import argparse
import operator
from operator import itemgetter
import sys, os, shutil
import os.path

##########################################################################################
# RETRIEVE USER INPUTS
##########################################################################################

#=========================================================================================
# create parser
#=========================================================================================
version_nb = "0.0.1"
parser = argparse.ArgumentParser(prog = 'xvg_average', usage='', add_help = False, formatter_class = argparse.RawDescriptionHelpFormatter, description =\
'''
**********************************************
v''' + version_nb + '''
author: Jean Helie (jean.helie@bioch.ox.ac.uk)
git: https://github.com/jhelie/xvg_average
**********************************************

[ DESCRIPTION ]
 
This script calculate the average of data contained in several xvg-like files.

The legend associated to the columns are used to identify the columns that should
be averaged together between the files.

[ REQUIREMENTS ]

The following python modules are needed :
 - numpy
 - scipy

[ NOTES ]

1. The xvg files need to have the same data columns (i.e. equal number of 
   columns and names) but these columns need not be in the same order within each
   file.

2. The first data column must be identical in all xvg files.

 
[ USAGE ]

Option	      Default  	Description                    
-----------------------------------------------------
-f			: xvg file(s)
-o		xvg_average	: name of outptut file
--skim		[1]	: outputs every X lines of the averaged xvg
--smooth	[1]	: calculate rolling average
--comments	[@,#]	: lines starting with these characters will be considered as comment

Other options
-----------------------------------------------------
--version		: show version number and exit
-h, --help		: show this menu and exit
 
''')

#options
parser.add_argument('-f', nargs='+', dest='xvgfilenames', help=argparse.SUPPRESS, required=True)
parser.add_argument('-o', nargs=1, dest='output_file', default=["xvg_average"], help=argparse.SUPPRESS)
parser.add_argument('--skim', nargs=1, dest='nb_skim', default=[1], type=int, help=argparse.SUPPRESS)
parser.add_argument('--smooth', nargs=1, dest='nb_smoothing', default=[1], type=int, help=argparse.SUPPRESS)
parser.add_argument('--comments', nargs=1, dest='comments', default=['@,#'], help=argparse.SUPPRESS)

#other options
parser.add_argument('--version', action='version', version='%(prog)s v' + version_nb, help=argparse.SUPPRESS)
parser.add_argument('-h','--help', action='help', help=argparse.SUPPRESS)

#=========================================================================================
# store inputs
#=========================================================================================

args = parser.parse_args()
args.output_file = args.output_file[0]
args.nb_skim = args.nb_skim[0]
args.nb_smoothing = args.nb_smoothing[0]

args.comments = args.comments.split(',')

#=========================================================================================
# import modules (doing it now otherwise might crash before we can display the help menu!)
#=========================================================================================

#generic science modules
try:
	import numpy
except:
	print "Error: you need to install the numpy module."
	sys.exit(1)
try:
	import scipy
	import scipy.stats
except:
	print "Error: you need to install the scipy module."
	sys.exit(1)

#=======================================================================
# sanity check
#=======================================================================

for f in args.xvgfilenames:
	if not os.path.isfile(f):
		print "Error: file " + str(f) + " not found."
		sys.exit(1)

if args.nb_skim < 1:
	print "Error: --skim must be greater than 0."
	sys.exit(1)

if args.nb_smoothing < 1:
	print "Error: --smooth must be greater than 0."
	sys.exit(1)

##########################################################################################
# FUNCTIONS DEFINITIONS
##########################################################################################

#=========================================================================================
# data loading
#=========================================================================================

def load_xvg():
	
	global nb_rows
	global nb_cols
	global first_col
	global files_columns
	global columns_names
	nb_rows = 0
	nb_cols = 0
	files_columns = {}
	columns_names = []
	
	print "Loading data..."	
	for f_index in range(0,len(args.xvgfilenames)):
		progress = '\r -reading file ' + str(f_index) + '/' + str(len(args.xvgfilenames)) + '                      '  
		sys.stdout.flush()
		sys.stdout.write(progress)
		filename = args.xvgfilenames[f_index]
		tmp_nb_rows_to_skip = 0
		files_columns[filename] = {"legend": {}}
		with open(filename) as f:
			lines = f.readlines()
			#determine legends and nb of lines to skip
			for l_index in range(0,len(lines)):
				line = lines[l_index]
				if line[-1] == '\n':
					line = line[:-1]
				if line[0] in args.comments:
					tmp_nb_rows_to_skip += 1
					if "legend length " not in line and "legend " in line:
						try:
							tmp_col = int(line.split("@ s")[1].split(" ")[0] + 1)
							tmp_name = line.split("legend \"")[1][:-1]
							files_columns[filename]["legend"][tmp_name] = tmp_col
						except:
							print "Error: unexpected data format in line " + str(l_index) + " in file " + str(filename) + "."
							print " -> " + str(line)
							sys.exit(1)
						if f_index == 0:
							if tmp_name in columns_names:
								print "Error: the legend '" + str(tmp_name) + "' is used twice in file " + str(filename) + "."
								sys.exit(1)
							else:
								columns_names.append(tmp_name)
						else:
							if tmp_name not in columns_names:
								print "Error: legend '" + str(tmp_name) + "' is present in file " + str(filename) + " but not in " + str(args.xvgfilenames[0]) + "."
								sys.exit(1)

			#get data
			files_columns[filename]["data"] = numpy.loadtxt(filename, skiprows = tmp_nb_rows_to_skip)
			
			#check that each file has the same number of data rows
			if f_index == 0:
				nb_rows = numpy.shape(files_columns[filename]["data"])[0]
			else:
				if numpy.shape(files_columns[filename]["data"])[0] != nb_rows:
					print "Error: file " + str(filename) + " has " + str(numpy.shape(files_columns[filename]["data"])[0]) + " data rows, whereas file " + str(args.xvgfilenames[0]) + " has " + str(nb_rows) + " data rows."
					sys.exit(1)
		
			#check that each file has the number of columns
			if f_index == 0:
				nb_cols = numpy.shape(files_columns[filename]["data"])[1]
			else:
				if numpy.shape(files_columns[filename]["data"])[1] != nb_cols:
					print "Error: file " + str(filename) + " has " + str(numpy.shape(files_columns[filename]["data"])[1]) + " data columns, whereas file " + str(args.xvgfilenames[0]) + " has " + str(nb_cols) + " data columns."
					sys.exit(1)
				
			#check that each file has the same first column
			if f_index == 0:
				first_col = files_columns[filename]["data"][:,0]
			else:
				if files_columns[filename]["data"][:,0] != first_col:
					print "Error: the first column of file " + str(filename) + " is different than that of " + str(args.xvgfilenames[0]) + "."
					sys.exit(1)
	return

#=========================================================================================
# core functions
#=========================================================================================

def rolling_avg(loc_list):												
	
	loc_arr = numpy.asarray(loc_list)
	shape = (loc_arr.shape[-1]-args.nb_smoothing+1,args.nb_smoothing)
	strides = (loc_arr.strides[-1],loc_arr.strides[-1])   	
	return numpy.average(numpy.lib.stride_tricks.as_strided(loc_arr, shape=shape, strides=strides), -1)
def calculate_average():

	global data_average
	
	#calculate raw average
	#---------------------
	data_average = numpy.zeros((nb_rows,nb_cols))
	data_average[:,0] = first_col
	for col_index in range(1, nb_cols):
		col_name = columns_names[col_index]
		for f_index in range(0,len(args.xvgfilenames)):
			filename = args.xvgfilenames[f_index]
			#NB this doesn't take the nan into account: first concatenate the columns than do a scipy nanmean on the rows
			data_average[:,col_index] +=  files_columns[filename]["data"][:,files_columns[filename]["legend"][col_name]]
			
		data_average[:,col_index] /= len(args.xvgfilenames)

	#update by smoothing
	#-------------------
	if args.nb_smoothing > 1:
		global data_average_smoothed
		data_average = numpy.zeros((XXX,nb_cols)) #determine XXX based on smoothing...
		
		for col_index in range(0, nb_cols):
			data_average_smoothed[:,col_index] = numpy.transpose(rolling_avg(numpy.transpose(data_average[:,col_index])))
			
	#update by skipping
	#------------------
	if args.nb_skim > 1 :
		#1. determine lenght of skimmed matrix
		#2. determine index (via floor/modulo similar to frames) of lines to keep
		#3. feel them in
	
	return

#=========================================================================================
# outputs
#=========================================================================================

def write_xvg():
	#put log file into the comment

	print "-writing average..."
	filename=os.getcwd() + '/' + str(out_filename)
	output_xvg = open(filename, 'w')
	output_xvg.write("@ title \"" + str(xvg_title) + "\"\n")
	output_xvg.write("@ xaxis  label \"time (ns)\"\n")
	output_xvg.write("@ autoscale ONREAD xaxes\n")
	output_xvg.write("@ TYPE XY\n")
	output_xvg.write("@ view 0.15, 0.15, 0.95, 0.85\n")
	output_xvg.write("@ legend on\n")
	output_xvg.write("@ legend box on\n")
	output_xvg.write("@ legend loctype view\n")
	output_xvg.write("@ legend 0.98, 0.8\n")
	output_xvg.write("@ legend length " + str(numpy.size(sizes)) + "\n")
	for l_index in range(0,numpy.size(sizes)):
		output_xvg.write("@ s" + str(l_index) + " legend \"" + str(sizes[l_index]) + "\"\n")
	
	#case: raw data points
	#---------------------
	if rolling_avg==-1:
		tmp_counter=0
		for t in sorted(data.iterkeys()):
			tmp_counter+=1		
			if tmp_counter==skip_every:
				#output results
				results=str(t)
				for l_index in range(0,numpy.size(sizes)):
					results+="	" + str(data[t][sizes[l_index]]/float(nb_files))
				results+="\n"
				output_xvg.write(results)
				#reset counter
				tmp_counter=0
	
	#case: running average
	#---------------------
	else:
		tmp_counter=0
		for t in sorted(data_avg.iterkeys()):
			tmp_counter+=1		
			if tmp_counter==skip_every:
				#output results
				results=str(t)
				for l_index in range(0,numpy.size(sizes)):
					results+="	" + str(data_avg[t][sizes[l_index]]/float(nb_files))
				results+="\n"
				output_xvg.write(results)
				#reset counter
				tmp_counter=0
	output_xvg.close()
	
	
	return

##########################################################################################
# MAIN
##########################################################################################


#exit
#====
sys.exit(0)
