import multiprocessing as mp
import numpy as np
import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt
from collections import deque
import numpy as np
from circBuff import circularNumpyBuffer

sampleSize=2000
bufferLen=100000

def testPipes(read_end, stop, outputShape):
	sampleSize=2000
	x = np.linspace(0, bufferLen, num=bufferLen)
	buffer = circularNumpyBuffer(bufferLen, np.float64)
	ax = plt.subplot()
	canvas = ax.figure.canvas
	while(not stop.is_set() and not read_end.poll(0.1)):
		continue
	data = read_end.recv()
	##############INIT PLOT#####################
	buffer.append(data)
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	fig.canvas.draw()   # note that the first draw comes before setting data 

	line, = ax.plot(buffer.acces(), x[:len(buffer)])
	# cache the background
	axbackground = fig.canvas.copy_from_bbox(ax.bbox)
	##############DONE INIT PLOT#####################
	while(not stop.is_set()):
		if(read_end.poll()):
			data = read_end.recv()
			buffer.append(data)
			line.set_ydata(buffer.acces())
			line.set_xdata(x[:len(buffer)])
			
			# recompute the ax.dataLim
			ax.relim()
			# update ax.viewLim using the new dataLim
			ax.autoscale_view()

		# restore background
		fig.canvas.restore_region(axbackground)

		# redraw just the points
		ax.draw_artist(line)

		# fill in the axes rectangle
		fig.canvas.blit(ax.bbox)
		# in this post http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
		# it is mentionned that blit causes strong memory leakage. 
		# however, I did not observe that.

		plt.pause(0.000000000001) 
		#plt.pause calls canvas.draw(), as can be read here:
		#http://bastibe.de/2013-05-30-speeding-up-matplotlib.html
		#however with Qt4 (and TkAgg??) this is needed. It seems,using a different backend, 
		#one can avoid plt.pause() and gain even more speed.
		