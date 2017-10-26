"""
This module provides a high level interface to the myDAQ. It can be used to aquire and/or generate signals on multiple channels or for feedback between channels, for this a custom feedback function needs to be passed. By default the aquired signals will be plotted and saved to file. If desired custom plot function can be provided. 
"""
import multiprocessing as mp
import threading
import sys
from functools import partial
import signal


from pydaq import simpleRead
from pydaq import feedback
from pydaq import plotThread

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
	"""class used for access to the mydaq, only one object of this class should be created"""
	def __init__(self):
		testIfName()
		
		self.stop = mp.Event()
		self.plot = False
		self.plotFunct = None
		self.plotHistory = 100000
		self.samplerate = 0
		self.nChannelsInData = 1
		self.saveData = False
		self.saveDataFormat = ""
		self.saveDataFilename = ""
		self.saveDataDelimiter = ""
		self.saveDataOverwrite = ""
		
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
			print("INCORRECT USAGE: you can not combine or use multiple of:")
			print("'onlyAquire', 'onlyGen', 'aquireAndGen', 'onlyFeedback' \t\tEXITING")
			sys.exit()
			return

	def setupInputPipes(self, plot, saveData):
		inputPipes = []
		if(plot):
			inputPipes.append(self.inputToPlot_write_end)
		if(saveData):
			inputPipes.append(self.inputToFile_write_end)
		return inputPipes

	def onlyAquire(self, inputChannels, plot=True, saveData=True, samplerate=1000, maxMeasure=[10,10], minMeasure=[-10,-10]):
		"""Configure the mydaq to aquire signals only, this function requires
		only one argument either a list of inputchannels as strings or a strings one inputchannel.
		
		For the mydaq the available input channels are: myDAQ1/ai1 and myDAQ1/ai0
		
		Optionally the samplerate, maxMeasurable voltage and minMeasurable
		voltage van be set as keyword arguments. MaxMeasure and minMeasure 
		can be passed as a single number, in which case the value is applied 
		to both all if there are multiple. 
		Or (when there are multiple input channels) as a list.
		
		A closer range between max and min measurable voltages gives a smaller error in the measurements.
		
		Examples:
		  pd.onlyAquire(["myDAQ1/ai1", "myDAQ1/ai0"])
		  pd.onlyAquire("myDAQ1/ai1")
		  pd.onlyAquire(["myDAQ1/ai0"]) #this form is also accepted
		  pd.onlyAquire("myDAQ1/ai1", samplerate=1000, maxMeasure=[10,10], minMeasure=[-10,-10])
		  pd.onlyAquire("myDAQ1/ai1", samplerate=1000, maxMeasure=10, minMeasure=-10)
		"""
		self.checkConfig()
		maxMeasure, minMeasure, inputChannels = self.checkIfValidArgs(samplerate, maxMeasure, minMeasure, inputChannels, "aquire", plot, saveData)
		self.rdy["aquisition"] = mp.Event()
		self.processes["aquisition"] = mp.Process(target = simpleRead.startReadOnly, 
			 args = (self.setupInputPipes(plot, saveData), self.stop, 
			 self.rdy["aquisition"], inputChannels, samplerate, maxMeasure, minMeasure,))
		self.configDone = True
		return

	def onlyGen(self, outputChannels, outputShape, samplerate=1000, maxGen=[10,10], minGen=[-10,-10]):
		self.checkConfig()
		maxMeasure, minMeasure, outputChannels = self.checkIfValidArgs(samplerate, maxGen, minGen, outputChannels, "gen", False, False)
		self.rdy["gen"] = mp.Event()
		self.processes["gen"] = mp.Process(target = simpleRead.startGenOnly, 
			 args = (self.output_read_end, self.stop, self.rdy["gen"], outputChannels, outputShape,
			 samplerate, maxMeasure, minMeasure,)) 
		self.configDone = True
		return
 
	#TODO expand for multi channels
	def aquireAndGen(self, inputChannels, outputChannels, outputShape, plot=True, saveData=True,
	samplerate=1000, maxMeasure=10, minMeasure=-10, finiteGen=False, nToMeasure=0):
		self.checkConfig()
		inputChannels, outputChannels, maxMeasure, minMeasure = self.checkIfValidArgs_fb(samplerate, maxMeasure, minMeasure, inputChannels, outputChannels, "onlyFeedback", plot, saveData)
		
		self.rdy["aquireAndGen"] = mp.Event()
		self.processes["aquireAndGen"] = mp.Process(target = simpleRead.startReadAndGen, 
			 args = (self.setupInputPipes(plot, saveData), self.output_read_end, self.stop, self.rdy["aquireAndGen"], outputChannels, outputShape,inputChannels, samplerate, maxMeasure, minMeasure, nToMeasure, finiteGen))  
		self.configDone = True
		return

	def onlyFeedback(self, inputChannels, outputChannels, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		self.checkConfig()
		inputChannels, outputChannels, maxMeasure, minMeasure = self.checkIfValidArgs_fb(samplerate, maxMeasure, minMeasure, inputChannels, outputChannels, "onlyFeedback", plot, saveData)
		self.rdy["onlyFeedback"] = mp.Event()
		self.processes["feedback"] = mp.Process(target = feedback.feedback, 
			 args = (self.setupInputPipes(plot, saveData), self.stop, self.rdy["onlyFeedback"], transferFunct, inputChannels, outputChannels, samplerate, maxMeasure, minMeasure,))
		self.configDone = True
		return

	# def FeedbackAndAquire(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		# pass #TODO

	# def FeedbackAndGen(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		# pass #TODO

	# def FeedbackGenAndAquire(self, transferFunct, plot=True, saveData=True, samplerate=1000, maxMeasure=10, minMeasure=-10):
		# pass #TODO

	def setCustomPlot(self, plotFunct):
		self.plotFunct = plotFunct
		return
	

	def setFileOptions(self, name="data", format="csv", overwrite=False, delimiter=", "):
		"""
		sets the name and format for the file the acquired data is written to.

		Parameters
		----------
		name : string, optional
			Name you want the output file to have. Use a filename that is compatible with your OS (No special characters allowed on windows for example). If the file exists new data will be appended at the end. Defaults to "data".

		format : string, optional
			Format of the data file, future versions of PyDAQ may expand the file types at the moment the only choice and default is "csv".

		Complete Example
		----------
		An example setting the name to "test" and the format to "csv"     
		::
			pd = pd.PyDAQ()

			configure
			pd.setFileOptions(name="test", format="csv")
			pd.onlyAquire(["myDAQ1/ai0", "myDAQ1/ai0"], samplerate=800, 
			maxMeasure=2, minMeasure=-2, plot=False, saveData=True)

			pd.begin()
			pd.menu()
			pd.end()
		"""
		self.saveDataFormat = format
		self.saveDataFilename = name
		self.saveDataDelimiter = delimiter
		self.saveDataOverwrite = overwrite
	def exit_gracefully(self, signal, frame):
		print('You pressed Ctrl+C!')
		self.end()
		sys.exit(0)

	def begin(self):
		#signal.signal(signal.SIGINT, self.exit_gracefully)		
		#print("setup signals")
		
		if(self.plot):
			if(self.plotFunct is None):
				if(self.samplerate > self.plotHistory):
					buflen = self.samplerate
				else:
					buflen = self.plotHistory
				self.processes["plotting"] = mp.Process(target = plotThread.plot, 
				args = (self.inputToPlot_read_end, self.stop, self.nChannelsInData,
				buflen,))
			else:
				self.processes["plotting"] = mp.Process(target = self.plotFunct, 
				args = (self.inputToPlot_read_end, self.stop,))
		if(self.saveData):
			self.processes["writeToFile"] = threading.Thread(target=plotThread.writeToFile, 
			args=(self.stop, self.inputToFile_read_end, self.saveDataFilename, self.saveDataFormat, self.saveDataOverwrite, self.saveDataDelimiter))
		for process in self.processes.values():
			# if(process is not None):
			process.start()
		#wait for all processes to report rdy so the menu can be run
		for rdy in self.rdy.values():
			# if(rdy is not None):
			rdy.wait()

	def signal_handler(signal, frame):
	    raise KeyboardInterrupt('SIGINT received')

	def menu(self):
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		try:
			input('Press Enter to stop\n')
		except (KeyboardInterrupt, SystemExit):
			self.end()
			sys.exit(0)

	def end(self):
		self.stop.set()
		for processName, process in self.processes.items():
			process.join()
			print("{0:15} {1}".format(processName+":", "stopped"))

	def checkIfValidArgs_fb(self, samplerate, maxMeasure, minMeasure, inputChannels, outputChannels, methodName, plot, saveData):
		
		def convertAndExpandArgs(arg, nIn, nOut):
			toReturn = []
			if(not isinstance(arg, list)): #x, x
				toReturn.append([arg] * nIn)
				toReturn.append([arg] * nOut)
			elif(not isinstance(arg[0], list)): #[x,x]
				toReturn.append(arg[0] * nIn)
				toReturn.append(arg[1] * nOut)
			return toReturn
		
		if(not isinstance(inputChannels, list)):
			inputChannels = [inputChannels]
		if(not isinstance(outputChannels, list)):
			outputChannels = [outputChannels]
		maxMeasure = convertAndExpandArgs(maxMeasure, len(inputChannels), len(outputChannels))
		minMeasure = convertAndExpandArgs(minMeasure, len(inputChannels), len(outputChannels))

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

		if(not 0 < samplerate <= 200000):
			print("WARNING: samplerate must be > 0 and <=200000 (for the myDAQ)")

		self.plot = plot
		self.saveData = saveData
		self.nChannelsInData = len(inputChannels)
		self.samplerate = samplerate
		
		return inputChannels, outputChannels, maxMeasure, minMeasure


	def checkIfValidArgs(self, samplerate, maxMeasure, minMeasure, channels, methodName, plot, saveData):
		
		def convertAndExpandArgs(arg, n):
			if(not isinstance(arg, list)):
				arg = [arg]
			while(n > len(arg)):
				arg.append(arg[-1])
			return arg

		
		if(not isinstance(channels, list)):
			n = 1
		else:
			n = len(channels)
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
		self.samplerate = samplerate

		return maxMeasure, minMeasure, channels
