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
		self.plot = False
		self.nChannelsInData = 1
		self.saveData = False
		self.configDone = False
		
		self.inputToPlot_write_end, self.inputToPlot_read_end = mp.Pipe()
		self.inputToFile_write_end, self.inputToFile_read_end = mp.Pipe()
		
		self.output_write_end, self.output_read_end = mp.Pipe()
		
		self.processes = {}
		self.rdy = {} 
		self.inputChannels = []
		self.activeChannels = {}

	def checkConfig(self):
		if(self.configDone):
			print("you can not combine or use multiple of:  'onlyAquire', 'onlyGen', 'aquireAndGen', 'onlyFeedback'")
			return

	def setupInputPipes(self, plot, saveData):
		inputPipes = []
		if(plot):
			inputPipes.append(self.inputToPlot_write_end)
		if(saveData):
			inputPipes.append(self.inputToFile_write_end)
		return inputPipes

	def onlyAquire(self, inputChannels, plot=True, saveData=True, samplerate=1000, maxMeasure=[10,10], minMeasure=[-10,-10]):
		self.checkConfig()
		maxMeasure, minMeasure, inputChannels = self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, inputChannels, "aquire", plot, saveData)
		self.rdy["aquisition"] = mp.Event()
		self.processes["aquisition"] = mp.Process(target = simpleRead.startReadOnly, 
			 args = (self.setupInputPipes(plot, saveData), self.stop, 
			 self.rdy["aquisition"], inputChannels, samplerate, maxMeasure, minMeasure,))
		self.configDone = True
		return

	def onlyGen(self, outputChannels, outputShape, samplerate=1000, maxMeasure=[10,10], minMeasure=[-10,-10]):
		self.checkConfig()
		maxMeasure, minMeasure, outputChannels = self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, outputChannels, "gen", False, False)
		self.rdy["gen"] = mp.Event()
		self.processes["gen"] = mp.Process(target = simpleRead.startGenOnly, 
			 args = (self.output_read_end, self.stop, self.rdy["gen"], outputChannels, outputShape,
			 samplerate, maxMeasure, minMeasure,)) 
		self.configDone = True
		return
 
	#TODO expand for multi channels
	def aquireAndGen(self, inputChannels, outputChannels, outputShape, plot=True, saveData=True,
	samplerate=1000, maxMeasure=10, minMeasure=-10):
		if(self.configDone):
			return
		samplerate, maxMeasure, minMeasure = self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, 
		inputChannels.append(outputChannels), "aquireAndGen")
		self.rdy["aquireAndGen"] = mp.Event()
		self.processes["aquireAndGen"] = mp.Process(target = simpleRead.startReadAndGen, 
			 args = (self.input_write_end, self.output_read_end, self.stop, self.rdy["aquireAndGen"],
			 outputChannel[0], outputShape,inputChannel[0], plot, saveData, samplerate, maxMeasure, minMeasure))  
		self.configDone = True
		return

	def onlyFeedback(self, channels, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		if(self.configDone):
			return
		maxMeasure, minMeasure, channels = self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, channels, "onlyFeedback", plot, saveData)
		print("samplerate: ",samplerate)
		self.rdy["onlyFeedback"] = mp.Event()
		self.processes["feedback"] = mp.Process(target = feedback.feedback, 
			 args = (self.setupInputPipes(plot, saveData), self.stop, self.rdy["onlyFeedback"], transferFunct, channels, samplerate, maxMeasure, minMeasure,))
		self.configDone = True
		return

	def FeedbackAndAquire(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def FeedbackAndGen(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def FeedbackGenAndAquire(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		pass #TODO

	def begin(self):
		if(self.plot):
			self.processes["plotting"] = mp.Process(target = plotThread.plot, 
			args = (self.inputToPlot_read_end, self.stop, self.nChannelsInData,))
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
		print("begin done\n")

	def menu(self):
		input('Press Enter to stop\n')

	def end(self):
		self.stop.set()
		for processName, process in self.processes.items():
			process.join()
			print("{0:15} {1}".format(processName+":", "stopped"))
	
	def checkIfValidArgs(self, samplerate, maxMeasure, minMeasure, channels, methodName, plot, saveData):
		
		def convertAndExpandArgs(arg, n):
			if(not isinstance(arg, list)):
				arg = [arg]
			while(n > len(arg)):
				arg.append(arg[-1])
			return arg

		def convertAndExpandArgs_feedback(arg, n):
			toReturn = []
			if(not isinstance(arg, list)): #x, x
				for i in range(n-1):
					print("appending",toReturn)
					toReturn.append([arg, arg])
			elif(not isinstance(arg[0], list)): #[x,x]
				toReturn.append(arg)
			return toReturn
			
		n = len(channels)
		if(methodName == "onlyFeedback"):
			if(not isinstance(channels[0], list)):
				channels = [channels]
			maxMeasure = convertAndExpandArgs_feedback(maxMeasure, n)
			print("MIN")
			minMeasure = convertAndExpandArgs_feedback(minMeasure, n)

			print(channels, samplerate, maxMeasure, minMeasure)

			for pair in maxMeasure:
				for V in pair:
					if(not -10 < V <= 10):
						print("WARNING: maxMeasure  must be > -10 and <= 10 (for the myDAQ)")
			for pair in minMeasure:
				for V in pair:
					if(not 10 > V >= -10):
						print("WARNING: minMeasure  must be <= -10 and < 10 (for the myDAQ)")
			for pairMax, pairMin in zip (maxMeasure, minMeasure):
				for Vmax, Vmin in zip(pairMax, pairMin):
					if(not Vmax > Vmin):
						print("WARNING: Vmax must be larger then Vmin")

		else:
			channels = convertAndExpandArgs(channels, n)
			self.inputChannels = channels
		
			maxMeasure = convertAndExpandArgs(maxMeasure, n)
			minMeasure = convertAndExpandArgs(minMeasure, n)

			for V in maxMeasure:
				if(not -10 < V <= 10):
					print("WARNING: maxMeasure  must be > -10 and <= 10 (for the myDAQ)")
			for V in minMeasure:
				if(not 10 > V >= -10):
					print("WARNING: minMeasure  must be <= -10 and < 10 (for the myDAQ)")
			for Vmax, Vmin in zip(maxMeasure, minMeasure):
				if(not Vmax > Vmin):
					print("WARNING: Vmax must be larger then Vmin")
		
		if(not 0 < samplerate <= 200000):
			print("WARNING: samplerate must be > 0 and <=200000 (for the myDAQ)")

		self.plot = plot
		self.saveData = saveData
		self.nChannelsInData = len(channels)

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

		return maxMeasure, minMeasure, channels
