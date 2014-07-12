################################################################################################################################################
# IMPORT MODULES
################################################################################################################################################

#import general python tools
import operator
from operator import itemgetter
import sys, os, shutil
import math

#import python extensions/packages to manipulate arrays
import numpy 				#to manipulate arrays
import scipy 				#mathematical tools and recipesimport MDAnalysis

################################################################################################################################################
# RETRIEVE USER INPUTS
################################################################################################################################################
#averagator_xvg.py $version $xvg_filename $pathname_1 $pathname_2 $pathname_3 $out_filename $rolling_avg $skip_every $xvg_title $nb_files
version=sys.argv[1]
xvg_filename=sys.argv[2]
pathname_1=sys.argv[3]
pathname_2=sys.argv[4]
pathname_3=sys.argv[5]
out_filename=sys.argv[6]
rolling_avg=int(sys.argv[7])
skip_every=int(sys.argv[8])
xvg_title=sys.argv[9]
nb_files=int(sys.argv[10])

################################################################################################################################################
# READ FILES DATA
################################################################################################################################################

#load files data
#---------------

data={}
sizes=[]
#1st file
#--------
print "-reading file 1..."
col_size_dict_1={}
#load data
file1=pathname_1+xvg_filename
with open(file1) as f:
	lines_1 = f.readlines()
#1st pass: creating data structure
for l in lines_1:
	l_noreturn=l[:-1]
	if l_noreturn[0]=="@":
		try:
			col_index=int(l_noreturn.split("@ s")[1].split(" ")[0])+1
			col_size_dict_1[col_index]=l_noreturn.split("legend \"")[1][:-1]
			sizes.append(l_noreturn.split("legend \"")[1][:-1])
		except:
			pass
	else:
		data[float(l_noreturn.split('\t')[0])]={}
		for size in col_size_dict_1.values():
			data[float(l_noreturn.split('\t')[0])][size]=0
#2nd pass: storing data
for l in lines_1:
	l_noreturn=l[:-1]
	if l_noreturn[0]!="@":
		columns=l_noreturn.split('\t')
		for c in range(1,len(columns)):
			data[float(columns[0])][col_size_dict_1[c]]+=float(columns[c])

#2nd file
#--------
if nb_files>1:
	print "-reading file 2..."
	col_size_dict_2={}
	#load data
	file2=pathname_2+xvg_filename
	with open(file2) as f:
		lines_2 = f.readlines()
	#1st pass: update column - size dict
	for l in lines_2:
		l_noreturn=l[:-1]
		if l_noreturn[0]=="@":
			try:
				col_index=int(l_noreturn.split("@ s")[1].split(" ")[0])+1
				col_size_dict_2[col_index]=l_noreturn.split("legend \"")[1][:-1]
			except:
				pass
		else:
			for size in col_size_dict_2.values():
				if size not in sizes:
					sizes.append(size)
					data[float(l_noreturn.split('\t')[0])][size]=0
	#2nd pass: storing data
	for l in lines_2:
		l_noreturn=l[:-1]
		if l_noreturn[0]!="@":
			columns=l_noreturn.split('\t')
			for c in range(1,len(columns)):
				data[float(columns[0])][col_size_dict_2[c]]+=float(columns[c])
			
#3rd file
#--------
if nb_files>2:
	print "-reading file 3..."
	col_size_dict_3={}
	#load data
	file3=pathname_3+xvg_filename
	with open(file3) as f:
		lines_3 = f.readlines()
	#1st pass: update column - size dict
	for l in lines_3:
		l_noreturn=l[:-1]
		if l_noreturn[0]=="@":
			try:
				col_index=int(l_noreturn.split("@ s")[1].split(" ")[0])+1
				col_size_dict_3[col_index]=l_noreturn.split("legend \"")[1][:-1]
			except:
				pass
		else:
			for size in col_size_dict_3.values():
				if size not in sizes:
					sizes.append(size)
					data[float(l_noreturn.split('\t')[0])][size]=0
	
	#2nd pass: storing data
	for l in lines_3:
		l_noreturn=l[:-1]
		if l_noreturn[0]!="@":
			columns=l_noreturn.split('\t')
			for c in range(1,len(columns)):
				data[float(columns[0])][col_size_dict_3[c]]+=float(columns[c])

################################################################################################################################################
# PERFORM AVERAGE IF NECESSARY
################################################################################################################################################

if rolling_avg>1:
	print "-performing rolling average..."
	data_avg={}
	#reset counters
	tmp_counter=0
	tmp_time_avg=[]
	tmp_data_avg={}
	for l_index in range(0,numpy.size(sizes)):
		tmp_data_avg[sizes[l_index]]=[]
	
	#browse data
	for t in sorted(data.iterkeys()):
		tmp_counter+=1
		
		#add data to current average
		tmp_time_avg.append(t)
		for l_index in range(0,numpy.size(sizes)):
			tmp_data_avg[sizes[l_index]].append(data[t][sizes[l_index]])
		
		#case: time to calculate the average
		if tmp_counter==rolling_avg:
			data_avg[numpy.average(tmp_time_avg)]={}
			for l_index in range(0,numpy.size(sizes)):
				data_avg[numpy.average(tmp_time_avg)][sizes[l_index]]=numpy.average(tmp_data_avg[sizes[l_index]])
			
			#reset counters
			tmp_counter=0
			tmp_time_avg=[]
			for l_index in range(0,numpy.size(sizes)):
				tmp_data_avg[sizes[l_index]]=[]


################################################################################################################################################
# OUTPUT AVERAGED XVG
################################################################################################################################################

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

#exit
#====
sys.exit(0)
