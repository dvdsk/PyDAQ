import multiprocessing as mp
import numpy as np
import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt
import numpy as np
from circBuff import circularNumpyBuffer

def writeToFile(stop, read_end, fileName, format):
	if(format=="text"):
		with open(fileName+'.csv','a+b') as f_handle:
			while(not stop.is_set()):
				if(read_end.poll(0.1)):
					data = read_end.recv()
					# print("DATA:")
					# print(data)
					np.savetxt(f_handle, data, fmt='%5.3f') #print every number as 5 characters with 3 decimals (millivolts range is abs accuracy of mydaq
				else:
					continue
	elif(format=="binairy"): #TODO
		with open(fileName+'.bin','a+b') as f_handle:
			while(not stop.is_set()):
				if(read_end.poll(0.1)):
					data = read_end.recv()
					np.save(f_handle, data)
				else:
					continue
	elif(format=="compressedBinairy"):
		pass #TODO

# def readFromFile(fileName, format):
#TODO

def waitForData(read_end, stop):
	while(not read_end.poll(0.1)):
		if(stop.is_set()):
			return
	print("getting data")

def setupLivePlot(ax, fig):
	canvas = ax.figure.canvas
	axbackground = fig.canvas.copy_from_bbox(ax.bbox) # cache the background
	fig.canvas.draw() #do a first draw before setting data 
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
	for line in lines.values():
		ax.draw_artist(line)

	# fill in the axes rectangle, this is a trick to speed
	# up matplotlib
	fig.canvas.blit(ax.bbox)

def plot(read_end, stop, bufferLen=100000):
	#this buffer is used to keep the last 'bufferLen' points
	#that have been send from the mydaq for plotting
	buffer1 = circularNumpyBuffer(bufferLen, np.float64)
	#buffer2 = circularNumpyBuffer(bufferLen, np.float64)
	
	#the x axis is just the number of points for now
	x = np.linspace(0, bufferLen, num=bufferLen)
	lines = {} #stores the data all the lines

	waitForData(read_end, stop)
	data = read_end.recv()#get the data
	buffer1.append(data)   #append it to the buffer
	#buffer2.append(data[1,:])   #append it to the buffer
	
	#Start the plot
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)
	
	#set things up for live plotting
	cachedPlotData = setupLivePlot(ax, fig)

	#add a new plot line (works just like plt.plot)
	#another possibility would be plt.scatter
	lines["plot1"], = ax.plot(buffer1.access(), x[:len(buffer1)])
	#lines["plot2"], = ax.plot(buffer2.access(), x[:len(buffer2)])
	
	#keep updating the plot until the program stops
	while(not stop.is_set()):
		#if there is new data, update the x and y data of the plots
		if(read_end.poll()):
			data = read_end.recv() #get the new data
			buffer1.append(data) #append it to the buffer
			#buffer2.append(data[1,:]) #append it to the buffer
			
			#send all the data (that now includes the new
			#data we recieved above ) to matplotlib. Do
			#this for every plot
			lines["plot1"].set_ydata(buffer1.access())
			lines["plot1"].set_xdata(x[:len(buffer1)])

			#lines["plot2"].set_ydata(buffer2.access())
			#lines["plot2"].set_xdata(x[:len(buffer2)])

			#update the view
			updateLivePlot(cachedPlotData,ax, fig, lines)
			
		#give matplotlib time to check if the user has zoomed in 
		#or done other things with the interface
		plt.pause(0.000000000001)