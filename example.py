import pyMyDAQ as pd
import numpy as np
#import yappi #Used for profiling code

from plotThread import waitForData, setupLivePlot, updateLivePlot
from circBuff import circularNumpyBuffer
from matplotlib import pyplot as plt

#een feedback funct
def transferFunct(buffer, feedbackSig):
	lenEven = len(buffer)//2*2
	V = buffer.access()[lenEven-2]
	R = V/((5-V)/1000)
	if(R > 822.5):
		feedbackSig[0] += 0.1
	else:
		feedbackSig[0] += 0.1
	
	feedbackSig[0] = 10
	# feedbackSig[1] = 10
	feedbackSig = np.clip(feedbackSig, -10, 10)
	return feedbackSig

def plot2(read_end, stop, nChannelsInData, bufferLen=100000):
	#this buffer is used to keep the last 'bufferLen' points
	#that have been send from the mydaq for plotting
	buffer = circularNumpyBuffer(bufferLen, np.float64)
	
	#the x axis is just the number of points for now
	x = np.linspace(0, bufferLen, num=bufferLen)
	lines = {} #stores the data all the lines
	waitForData(read_end, stop)
	data = read_end.recv()#get the data
	buffer.append(data[:,0])  #append it to the buffer
	
	#Start the plot
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)
	
	#set things up for live plotting
	cachedPlotData = setupLivePlot(ax, fig)

	#add a new plot line (works just like plt.plot)
	#another possibility would be plt.scatter
	lines["plot1"], = ax.plot(buffer.access(), x[:len(buffer)])
	
	#keep updating the plot until the program stops
	while(not stop.is_set()):
		#if there is new data, update the x and y data of the plots
		if(read_end.poll()):
			print("test")
			data = read_end.recv()#get the data
			buffer.append(data[:,0])
			
			#send all the data (that now includes the new
			#data we recieved above ) to matplotlib. Do
			#this for every plot
			lines["plot1"].set_ydata(buffer.access())
			lines["plot1"].set_xdata(x[:len(buffer)])

			#update the view
			updateLivePlot(cachedPlotData,ax, fig, lines)
			
		#give matplotlib time to check if the user has zoomed in 
		#or done other things with the interface
		plt.pause(0.000000000001)


outputShape = np.sin(np.linspace(0, 2*np.pi, num =2000, endpoint=False, dtype=np.float64))

if __name__ == '__main__':
#yappi.start()
	
	pd = pd.PyDAQ()
	#pd.setCustomPlot(plot2)
	pd.setFileOptions(name="testData", format="csv")
	# pd.onlyFeedback(["myDAQ1/ai1", "myDAQ1/ai0"],["myDAQ1/ao1", "myDAQ1/ao0"], transferFunct)
	#pd.onlyFeedback("myDAQ1/ai1","myDAQ1/ao1", transferFunct)
	#pd.onlyGen(["myDAQ1/ao1", "myDAQ1/ao0"], outputShape)
	#pd.onlyAquire(["myDAQ1/ai1", "myDAQ1/ai0"])
	pd.aquireAndGen(["myDAQ1/ai1","myDAQ1/ai0"], ["myDAQ1/ao1","myDAQ1/ao0"], outputShape, samplerate=200000)
	#pd.aquireAndGen(["myDAQ1/ai1"], ["myDAQ1/ao1"], outputShape)
	
	
	pd.begin()
	pd.menu()
	pd.end()
	
#yappi.stop()
#print(yappi.get_func_stats() )