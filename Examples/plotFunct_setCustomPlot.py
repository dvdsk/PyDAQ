import pydaq
import pydaq.plotThread as pdPlot

import numpy as np
import matplotlib.pyplot as plt

def plotFunct(read_end, stop):
	#this buffer is used to keep the last 10000 points
	#that have been send from the mydaq for plotting
	buffer = pdPlot.circularNumpyBuffer(10000, np.float64)
	
	#the x axis is just the number of points for now
	x = np.linspace(0, 10000, num=10000)
	lines = [] #stores the data all the lines
	pdPlot.waitForData(read_end, stop)
	data = read_end.recv()#get the data
	buffer.append(data[:,0])  #append it to the buffer
	
	#Start the plot
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)
	
	#set things up for live plotting
	cachedPlotData = pdPlot.setupLivePlot(ax, fig)

	#add a new plot line (works just like plt.plot)
	#returns a list of lines that were added we merge that with the existing lines
	lines += ax.plot(buffer.access(), x[:len(buffer)])
	
	#keep updating the plot until the program stops
	while(not stop.is_set()):
		#if there is new data, update the x and y data of the plots
		if(read_end.poll()):
			data = read_end.recv()#get the data
			buffer.append(data[:,0])
			
			#send all the data (that now includes the new
			#data we recieved above ) to matplotlib. Do
			#this for every plot
			lines[0].set_ydata(buffer.access())
			lines[0].set_xdata(x[:len(buffer)])

			#update the view
			pdPlot.updateLivePlot(cachedPlotData,ax, fig, lines)
			
		#give matplotlib time to check if the user has zoomed in 
		#or done other things with the interface
		plt.pause(0.000000000001)

if __name__ == '__main__':

	pd = pydaqmx.PyDAQ()

	#configure
	pd.setCustomPlot(plotFunct)
	pd.onlyAquire("myDAQ1/ai0", 
	  samplerate=800, maxMeasure=2, minMeasure=-2,
	  plot=True, saveData=True)

	pd.begin()
	pd.menu()
	pd.end()