import multiprocessing as mp
import numpy as np
import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt
from collections import deque
import numpy as np

class circularNumpyBuffer:
	
	def __init__(self, capacity, dtype=float):
		self.arr = np.empty(capacity*10, dtype)
		self.arrLen = capacity*10
		self.left_index = 0
		self.right_index = 0
		self.capacity = capacity
	def append(self,sample):
		if(self.right_index+len(sample)<self.arrLen):
			#enough space left for the sample in the buffer
			usedCapacity = self.right_index-self.left_index
			self.arr[self.right_index : self.right_index+len(sample)] = sample
			if(usedCapacity + len(sample) > self.capacity):
				#time to start 'wiping data' to prevent buffer from growing to large
				self.left_index += np.size(sample)
			self.right_index += np.size(sample)
		else:
			#if out of space copy all still usefull data to the beginning
			newLeft = self.left_index+np.size(sample)
			print("len:",self.right_index-newLeft)
			self.arr[0:(self.right_index - newLeft)] = self.arr[newLeft:self.right_index]
			#update index
			self.right_index = self.right_index - newLeft
			self.left_index = 0
			#store sample
			self.arr[self.right_index : np.size(sample)] = sample
			self.right_index += np.size(sample)
	def acces(self):
		print(self.left_index)
		print(self.right_index)
		return self.arr[self.left_index : self.right_index]
	def __len__(self):
		return self.right_index-self.left_index


def testPipes(read_end, stop, outputShape):
	sampleSize=2000
	buffer = circularNumpyBuffer(100000, np.float64)
	ax = plt.subplot()
	canvas = ax.figure.canvas
	while(not stop.is_set() and not read_end.poll(0.1)):
		continue
	data = read_end.recv()
	##############INIT PLOT#####################
	buffer.append(data)
	print(buffer.acces())
	x = np.linspace(0, 100000, num=100000)
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	fig.canvas.draw()   # note that the first draw comes before setting data 

	line, = ax.plot(buffer.acces(), x[:len(buffer)])
	# cache the background
	axbackground = fig.canvas.copy_from_bbox(ax.bbox)
	##############DONE INIT PLOT#####################
	print("now in forever loopy loopy without break")
	while(not stop.is_set()):
		if(read_end.poll()):
			data = read_end.recv()
			buffer.append(data)
			line.set_ydata(buffer.acces())
			line.set_xdata(x[:len(buffer)])

			print("len buffer: ", len(buffer), "len x: ",len(x[:len(buffer)]))
			print(buffer)
			
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