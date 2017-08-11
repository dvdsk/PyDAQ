import multiprocessing as mp

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
	data = read_end.recv()
	line, = plt.plot(outputShape, data, animated=True)
	background = canvas.copy_from_bbox(ax.bbox)
	canvas.draw()
	
	print("now in forever loopy loopy without break")
	while(not stop.is_set()):
		if(read_end.poll(0.1)):
			data = read_end.recv()
			canvas.restore_region(background)
			line.set_ydata(data)
			ax.draw_artist(line)
			canvas.blit(ax.bbox)
			#plt.draw()
			plt.pause(0.0001)
			print("loop loop")
	plt.show()
	print("testPipes rdy to join")