#import multiprocessing as mp
import numpy as np
from pydaq.circBuff import circularNumpyBuffer
#import matplotlib
#matplotlib.use('GTKAgg')

#this code hides matplotlib deprecation warnings
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore",category=matplotlib.cbook.mplDeprecation)

#import matplotlib with warnings no suppressed
from matplotlib import pyplot as plt

def writeToFile(stop, read_end, fileName, format):
	if(format=="csv"):
		with open(fileName+'.csv','a+b') as f_handle:
			while(not stop.is_set()):
				if(read_end.poll(0.1)):
					data = read_end.recv()
					np.savetxt(f_handle, data, fmt='%5.3f') #print every number as 5 characters with 3 decimals (millivolts range is abs accuracy of mydaq
				else:
					continue
	elif(format=="npy"): #TODO
		with open(fileName+'.bin','a+b') as f_handle:
			while(not stop.is_set()):
				if(read_end.poll(0.1)):
					data = read_end.recv()
					np.save(f_handle, data)
				else:
					continue
	elif(format=="npz"):
		pass #TODO

# def readFromFile(fileName, format):
#TODO

def waitForData(read_end, stop):
	while(not read_end.poll(0.1)):
		if(stop.is_set()):
			return

def setupLivePlot(ax, fig):
	canvas = ax.figure.canvas
	axbackground = fig.canvas.copy_from_bbox(ax.bbox) # cache the background
	canvas.draw() #do a first draw before setting data 
	return axbackground

def updateLivePlot(axbackground, ax, fig, lines):
	# update the axis limits
	ax.relim()
	# autoscale the view so all data fits
	# this will stop when the user has moved 
	# around in the view manually.
	ax.autoscale_view()
	
	# restore background, this is a trick to speed
	# up matplotlib
	fig.canvas.restore_region(axbackground)

	# redraw just the points
	for line in lines:
		ax.draw_artist(line)

	# fill in the axes rectangle, this is a trick to speed
	# up matplotlib
	fig.canvas.blit(ax.bbox)

def plot(read_end, stop, nChannelsInData, bufferLen):
	#this buffer is used to keep the last 'bufferLen' points
	#that have been send from the mydaq for plotting
	buffers = []
	for n in range(nChannelsInData):
		buffers.append(circularNumpyBuffer(bufferLen, np.float64))
	
	#the x axis is just the number of points for now
	x = np.linspace(0, bufferLen, num=bufferLen)
	waitForData(read_end, stop)
	data = read_end.recv()#get the data
	if(nChannelsInData == 1):
		buffers[0].append(data)
	else:
		for i, buffer in enumerate(buffers):
			buffer.append(data[:,i])  #append it to the buffer
	
	#Start the plot
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)
	
	#set things up for live plotting
	cachedPlotData = setupLivePlot(ax, fig)

	#add a new plot line (works just like plt.plot)
	#another possibility would be plt.scatter
	lines = []
	for i, buffer in enumerate(buffers):
		lines += ax.plot(buffer.access(), x[:len(buffer)])
	
	#keep updating the plot until the program stops
	while(not stop.is_set()):
		#if there is new data, update the x and y data of the plots
		if(read_end.poll()):
			data = read_end.recv()#get the data
			if(nChannelsInData == 1):
				buffer.append(data)	
			else:
				for i, buffer in enumerate(buffers):
					buffer.append(data[:,i])
			
			#send all the data (that now includes the new
			#data we recieved above ) to matplotlib. Do
			#this for every plot
			for line, buffer in zip(lines, buffers):
				line.set_ydata(buffer.access())
				line.set_xdata(x[:len(buffer)])

			#update the view
			updateLivePlot(cachedPlotData,ax, fig, lines)
			
		#give matplotlib time to check if the user has zoomed in 
		#or done other things with the interface
		plt.pause(0.000000000001)