import multiprocessing as mp
import numpy as np
import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt
from collections import deque

# class Plot:
	# def __init__(self, x, y):
		# self.fig, self.ax = plt.subplots(1, 1)
		# self.ax.set_aspect('equal')
		# self.ax.set_xlim(0, 255)
		# self.ax.set_ylim(0, 255)
		# self.ax.set_xlabel("input signal (volt)")
		# self.ax.set_ylabel("output signal (volt)")
		# self.ax.hold(True)
		# plt.ion()
		# self.background = self.fig.canvas.copy_from_bbox(self.ax.bbox)
		# self.points = self.ax.plot(x,y, 'o')[0]
		
	# def update(self, x ,y):
		# self.points.set_data(x, y)

		# # restore background
		# self.fig.canvas.restore_region(self.background)
		# # redraw just the points
		# self.ax.draw_artist(self.points)
		# # fill in the axes rectangle
		# self.fig.canvas.blit(self.ax.bbox)
	# def __exit__(self):
		# plt.close(self.fig)

 
		
def testPipes(read_end, stop, outputShape):
	buffer = deque(maxlen=10000) 
	print(buffer)
	ax = plt.subplot()
	canvas = ax.figure.canvas
	while(not stop.is_set() and not read_end.poll(0.1)):
		continue
	data = read_end.recv()
	##############INIT PLOT#####################
	#buffer.append(np.mean(data))
	buffer.append(data.mean())
	x = np.linspace(0, 10000, num=10000)
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	fig.canvas.draw()   # note that the first draw comes before setting data 

	line, = ax.plot(x[:len(buffer)], lw=3)
	line.set_ydata(buffer)

	# cache the background
	axbackground = fig.canvas.copy_from_bbox(ax.bbox)
	##############DONE INIT PLOT#####################
	print("now in forever loopy loopy without break")
	while(not stop.is_set()):
		if(read_end.poll()):
			data = read_end.recv()
			buffer.append(data.mean())
			line.set_ydata(buffer)
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