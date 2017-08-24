"""MAIN FILE"""
import multiprocessing as mp
import numpy as np
import sys

import simpleRead
import feedback
import plotThread

"""
See documentation at: http://zone.ni.com/reference/en-XX/help/370471AA-01/

-Constants are imported from PyDAQmx.DAQmxConstants

-Variables that are not pointers can be used directly,
as they will be automatically converted by ctypes

-For pointers, first declare them and then use byref() 
to pass by referenceNULL in C becomes None in Python
"""

def testProcess(cv):
	cv.set()
	return

def testIfName():
	cv = mp.Event()
	tp = mp.Process(target=testProcess, args = (cv,))
	try:
		tp.start()
	except RuntimeError as e:
		print("CRITICAL ERROR: you forgot to nest your code in: \"'if __name__ == '__main__':\"")
		print("this would cause a crash later in this module")
	else:
		tp.join()
	if(not cv.is_set()):
		sys.exit()

class PyDAQ:
	"""description"""
	def __init__(self):
		testIfName()
		
		self.stop = mp.Event()
		self.rdy = mp.Event()
		
		self.input_write_end, self.input_read_end = mp.Pipe()
		self.output_write_end, self.output_read_end = mp.Pipe()
		
		self.plotting_thread = None
		self.aquisition_thread = None
		self.feedback_thread = None

	def plot(self):
		self.plotting_thread = mp.Process(target = plotThread.plot, 
                      args = (self.input_read_end, self.stop, self.rdy,))

	def aquisition(self, outputShape):
		if(self.feedback_thread is not None):
			print("WARNING: You can not run both feedback and aquisition at the same time, "
				 +"not starting aquisition")
		else:
			outputshape = np.full(0, 200, dtype = np.float64)
			self.aquisition_thread = mp.Process(target = simpleRead.startCallBack, 
			     args = (self.input_write_end, self.output_read_end, 
			     self.stop, outputShape,)) 

	def Feedback(self, transferFunct):
		if(self.aquisition_thread is not None):
			print("WARNING: You can not run both feedback and aquisition at the same time, "
				 +"not starting feedback")
		else:
			self.feedback_thread = mp.Process(target = feedback.feedback, 
			     args = (self.input_write_end, self.stop, transferFunct,))

	def begin(self):
		if(self.aquisition_thread is not None):
			self.aquisition_thread.start()
		if(self.plotting_thread is not None):
			self.plotting_thread.start()
		if(self.feedback_thread is not None):
			self.feedback_thread.start()

	def menu(self):
		self.rdy.wait()
		input('Press Enter to stop\n')

	def end(self):
		self.stop.set()
		if(self.feedback_thread is not None):
			self.feedback_thread.join()
		if(self.aquisition_thread is not None):
			self.aquisition_thread.join()
		if(self.plotting_thread is not None):
			self.plotting_thread.join()

