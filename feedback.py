import multiprocessing as mp

from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxTypes import *
from PyDAQmx.DAQmxFunctions import DAQError
import numpy as np
from circBuff import circularNumpyBuffer
import time

# from main import transferFunct

"""
See documentation at: http://zone.ni.com/reference/en-XX/help/370471AA-01/

-Constants are imported from PyDAQmx.DAQmxConstants

-Variables that are not pointers can be used directly,
as they will be automatically converted by ctypes

-For pointers, first declare them and then use byref() 
to pass by referenceNULL in C becomes None in Python
"""
class ReadTask(Task):
	def __init__(self, inputChannel, samplerate, maxMeasure, minMeasure):
		Task.__init__(self)
		self.data = np.empty(200)
		self.a = []
		self.rdy = True
		
		#configurate input channel, where we read the ouput from the myDAQ
		try:
			self.CreateAIVoltageChan(
				inputChannel, #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
				"", #name to assign to virt channel mapped to phys channel above
				DAQmx_Val_Cfg_Default, #measurement technique used
				minMeasure, #min value expected to measure
				maxMeasure, #max value expected to measure
				DAQmx_Val_Volts, #units for min val and max val
				None) #name of custom scale if used
		except DAQError:
			print("CRITICAL: INCORRECT inputChannel ("+inputChannel+"), is there a mydaq connected?, "
				 +"are you specifing an inputChannel?")
			self.rdy = False
			return
			
		#configurate timing and sample rate for the samples
		self.CfgSampClkTiming(
			"", #source terimal of Sample clock ("" means onboard clock)
			samplerate, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #aquire on rising edge of sample clock
			DAQmx_Val_ContSamps, #aquire continues until task stopped
			samplerate) #numb to aquire if finitSamps/ bufferSize if contSamps (bufsize in this case)

class WriteTask(Task):
	def __init__(self, outputChannel, maxMeasure, minMeasure):
		Task.__init__(self)
		self.sampswritten = int32()
		self.a = []
		self.rdy = True
		
		#configurate output channel, this is the signal the myDAQ outputs
		try:
			self.CreateAOVoltageChan(
				outputChannel, #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
				"", #name to assign to virt channel mapped to phys channel above
				minMeasure, #min value expected to output
				maxMeasure, #max value expected to output
				DAQmx_Val_Volts, #units for min val and max val
				None) #name of custom scale if used
		except DAQError:
			print("CRITICAL: INCORRECT outputChannel ("+outputChannel+"), is there a mydaq connected?, "
				 +"are you specifing an outputChannel?")
			self.rdy = False
			return
#not configuring sample timing -> driver in on demand sample for anolog out

def feedback(input_write_ends, stop, rdy, transferFunct, channels, samplerate, maxMeasure, minMeasure):
	buffer = circularNumpyBuffer(10000, dtype=np.float64) #TODO expose to user (len)
	data = np.empty(samplerate, dtype=np.float64)
	sampsWritten = int32()
	sampsRead = int32()
	
	sendbuf = np.empty(200*2)
	start_idx = 0

	t0 = time.time()
	for channelPair, maxMeasurePair, minMeasurePair, in zip(channels, maxMeasure, minMeasure):
		readTask = ReadTask(channelPair[0], samplerate, maxMeasurePair[0], minMeasurePair[0])
		writeTask = WriteTask(channelPair[1], maxMeasurePair[1], minMeasurePair[1])
	if(readTask.rdy == False or writeTask.rdy == False):
		print("errors detected, not starting readout!!")
		return 
	
	feedbackSig = np.full(len(channels), 0, dtype=np.float64)
	start_idx= 0
	rdy.set()
	
	while(not stop.wait(0)):
		t0
		t1 = time.time()
		if(t1-t0 >0.011):
			print("latency:",t1-t0)
		readTask.ReadAnalogF64(
			DAQmx_Val_Auto, #read as many samples as there are in the buffer
			0, #timeout in seconds
			DAQmx_Val_GroupByScanNumber, #read entire channel in one go
			data, #array where the samples should be put in
			200, #number of samples
			byref(sampsRead), #reference where to store: numb of samples read
			None)
		if(sampsRead.value != 0): 
			buffer.append(data[0:sampsRead.value])
			if(start_idx > 200-1):
				print("sending")
				start_idx_even = start_idx//2*2 #round down to even number
				tosend = sendbuf[0:start_idx_even]
				tosend = tosend.reshape(len(channels), len(tosend)//len(channels))
				for write_end in input_write_ends:
					write_end.send(tosend)
				start_idx -= start_idx_even
			else:
				print(sampsRead.value)
				sendbuf[start_idx:start_idx+sampsRead.value] = data[0:sampsRead.value]
				start_idx+=sampsRead.value
			
			#TODO check needed?
			feedbackSig = transferFunct(buffer, feedbackSig)
			writeTask.WriteAnalogF64(
				1, #number of samples to write per channel
				True, #start output automatically
				1, #timeout to wait for funct to write samples 
				DAQmx_Val_GroupByScanNumber, #read entire channel in one go
				feedbackSig, #source array from which to write the data
				byref(sampsWritten),  #variable to store the numb of written samps in
				None)
			t0 = t1

	#shutdown routine
	#start by setting the output signal to zero
	writeTask.StopTask()
	writeTask.WriteAnalogF64(
		1, #number of samples to write per channel
		True, #start output automatically
		1, #timeout to wait for funct to write samples 
		DAQmx_Val_GroupByChannel, #read entire channel in one go
		np.full(len(channels), 0, dtype=np.float64), #source array from which to write the data
		byref(sampsWritten),  #variable to store the numb of written samps in
		None)
	
	readTask.StopTask()
	writeTask.StopTask()
	readTask.ClearTask()
	writeTask.ClearTask()
	print("myDAQ shut down succesfully\n")