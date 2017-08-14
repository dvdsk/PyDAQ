import multiprocessing as mp
import numpy as np
import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt
from collections import deque
import numpy as np

class circularNumpyBuffer:
	"""A numpy implementation of a circular buffer, a circular buffer can append data forever
	   but starts overwriting old data after its capacity is reached. It thus only remembers the
	   last data. This simple implementation has no check on the appending data, make sure
	   it is not larger then the capacity of this buffer. It is only capable of appending numpy arrays
	   not other data.
	"""
	def __init__(self, capacity, dtype=np.float64):
		#internal buffer is 10x larger to minimise the amount of move operations needed
		self.arrLen = capacity*10
		self.arr = np.empty(self.arrLen, dtype)

		#indexes used to keep track of where the current data is
		self.left_index = 0
		self.right_index = 0
		self.capacity = capacity
	def append(self,sample):
		#check if we have enough space left in the array
		if(self.right_index+len(sample)<self.arrLen):
			#copy the new data into the array
			usedCapacity = self.right_index-self.left_index
			self.arr[self.right_index : self.right_index+len(sample)] = sample
			#check if we are at capacity and need to 'forget' some data by shifting the left index
			if(usedCapacity + len(sample) > self.capacity):
				self.left_index += np.size(sample)
			self.right_index += np.size(sample)
		else:
			#start by forgetting the data we no longer need
			newLeft = self.left_index+np.size(sample)
			#copy the data from the end of the array to the start so we have enough space again
			self.arr[0:(self.right_index - newLeft)] = self.arr[newLeft:self.right_index]
			#update indexes reflecting we now start at the beginning of the array
			self.right_index = self.right_index - newLeft
			self.left_index = 0
			#store sample and update right index 
			#left index does not need updating as we started by updating left/forgetting some data
			#and took this into account when moving data back to the the start of the array
			self.arr[self.right_index : np.size(sample)] = sample
			self.right_index += np.size(sample)
	def acces(self):
		print(self.left_index)
		print(self.right_index)
		return self.arr[self.left_index : self.right_index]
	def __len__(self):
		return self.right_index-self.left_index

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
		
	print("testPipes rdy to join")