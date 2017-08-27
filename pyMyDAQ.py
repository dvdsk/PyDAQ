"""MAIN FILE"""
import multiprocessing as mp
import threading
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
		print("this would cause a crash later in this module exiting")
	else:
		tp.join()
	if(not cv.is_set()):
		sys.exit()

class PyDAQ:
	"""description"""
	def __init__(self):
		testIfName()
		
		self.stop = mp.Event()
		self.plot = None
		self.saveData = None
		self.configDone = False
		
		self.inputToPlot_write_end, self.inputToPlot_read_end = mp.Pipe()
		self.inputToFile_write_end, self.inputToFile_read_end = mp.Pipe()
		
		self.output_write_end, self.output_read_end = mp.Pipe()
		
		self.processes = {}
		self.rdy = {} 
		self.activeChannels = {}

	def setupInputPipes(self, plot, saveData):
		inputPipes = []
		if(plot):
			inputPipes.append(self.inputToPlot_write_end)
		if(saveData):
			inputPipes.append(self.inputToFile_write_end)
		return inputPipes

	def onlyAquire(self, inputChannel, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		if(self.configDone):
			print("you can not combine or use multiple of:  'onlyAquire', 'onlyGen', 'aquireAndGen', 'onlyFeedback'")
			return
		self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, [inputChannel], "aquire", plot, saveData)
		self.rdy["aquisition"] = mp.Event()
		self.processes["aquisition"] = mp.Process(target = simpleRead.startReadOnly, 
			 args = (self.setupInputPipes(plot, saveData), self.stop, 
			 self.rdy["aquisition"], inputChannel, samplerate, maxMeasure, minMeasure,)) 
		self.configDone = True
		return

	def onlyGen(self, outputChannel, outputShape, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		if(self.configDone):
			return
		self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, [outputChannel], "gen")
		self.rdy["gen"] = mp.Event()
		self.processes["gen"] = mp.Process(target = simpleRead.startGenOnly, 
			 args = (self.output_read_end, self.stop, self.rdy["gen"], outputChannel, outputShape,
			 plot, saveData, samplerate, maxMeasure, minMeasure,)) 
		self.configDone = True
		return
 
	#TODO expand for multi channels
	def aquireAndGen(self, inputChannels, outputChannels, outputShape, plot=True, saveData=True,
	samplerate=1000, maxMeasure=10, minMeasure=-10):
		if(self.configDone):
			return
		self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, 
		inputChannels.append(outputChannels), "aquireAndGen")
		self.rdy["aquireAndGen"] = mp.Event()
		self.processes["aquireAndGen"] = mp.Process(target = simpleRead.startReadAndGen, 
			 args = (self.input_write_end, self.output_read_end, self.stop, self.rdy["aquireAndGen"],
			 outputChannel[0], outputShape,inputChannel[0], plot, saveData, samplerate, maxMeasure, minMeasure))  
		self.configDone = True
		return

	def onlyFeedback(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		if(self.configDone):
			return
		self.checkIfValidArgs(samplerate, maxMeasure, minMeasure,  "feedback")
		self.rdy["feedback"] = mp.Event()
		self.processes["feedback"] = mp.Process(target = feedback.feedback, 
			 args = (self.input_write_end, self.stop, transferFunct,inputChannel, 
			         outputChannel, plot, saveData, samplerate, maxMeasure, minMeasure,))
		self.configDone = True
		return

	def FeedbackAndAquire(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def FeedbackAndGen(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def FeedbackGenAndAquire(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def DoubleFeedback(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def begin(self):
		if(self.plot):
			self.processes["plotting"] = mp.Process(target = plotThread.plot, 
			args = (self.inputToPlot_read_end, self.stop,))
		if(self.saveData):
			self.processes["writeToFile"] = threading.Thread(target=plotThread.writeToFile, 
			args=(self.stop, self.inputToFile_read_end, "test", "text"))
		for process in self.processes.values():
			# if(process is not None):
			process.start()
		#wait for all processes to report rdy so the menu can be run
		for rdy in self.rdy.values():
			# if(rdy is not None):
			rdy.wait()

	def menu(self):
		input('Press Enter to stop\n')

	def end(self):
		self.stop.set()
		for processName, process in self.processes.items():
			# if(process is not None):
			process.join()
			print("{0:15} {1}".format(processName+":", "stopped"))
	
	def checkIfValidArgs(self, samplerate, maxMeasure, minMeasure, channels, methodName, plot, saveData):
		if(not -10 < maxMeasure <= 10):
			print("WARNING: maxMeasure  must be > -10 and <= 10 (for the myDAQ)")
		if(not 10 > minMeasure >= -10):
			print("WARNING: minMeasure  must be <= -10 and < 10 (for the myDAQ)")
		if(not 0 < samplerate <= 200000):
			print("WARNING: samplerate must be > 0 and <=200000 (for the myDAQ)")
		
		self.plot = plot
		self.saveData = saveData
		
		#check if the inputs are valid
		for channel in channels:
			if(type(channel) == str()):
				if(channel in self.activeChannels.keys()):
					print("ERROR: channel ("+channel+") is already in use by: "+
					self.activeChannels[channel][methodName]+"!")
				else:
					self.activeChannels[channel] = {}
					self.activeChannels[channel]["methodName"][methodName]
					self.activeChannels[channel]["sampleRate"][samplerate]
					self.activeChannels[channel]["maxMeasure"][maxMeasure]
					self.activeChannels[channel]["minMeasure"][minMeasure]
