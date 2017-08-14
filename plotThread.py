import multiprocessing as mp
import numpy as np
import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib import pyplot as plt

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
	ax = plt.subplot()
	canvas = ax.figure.canvas
	while(not stop.is_set() and not read_end.poll(0.1)):
		continue
		
	##############INIT PLOT#####################
	k=0.
	x = np.linspace(0,50., num=10000)
	fig = plt.figure()
	ax = fig.add_subplot(1, 1, 1)

	fig.canvas.draw()   # note that the first draw comes before setting data 

	line, = ax.plot(x, lw=3)
	ax.set_ylim([-1,1])


	# cache the background
	axbackground = fig.canvas.copy_from_bbox(ax.bbox)
	##############DONE INIT PLOT#####################
	
	print("now in forever loopy loopy without break")
	while(not stop.is_set()):
		if(read_end.poll()):
			data = read_end.recv()
			
		line.set_ydata(np.sin(x/3.+k))
		#print tx
		k+=0.11

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