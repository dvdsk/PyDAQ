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
	def __init__(self):
		Task.__init__(self)
		self.data = np.empty(200)
		self.a = []
		self.rdy = True
		
		#configurate input channel, where we read the ouput from the myDAQ
		try:
			self.CreateAIVoltageChan(
				"myDAQ1/ai0", #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
				"", #name to assign to virt channel mapped to phys channel above
				DAQmx_Val_Cfg_Default, #measurement technique used
				-10.0, #min value expected to measure
				10.0, #max value expected to measure
				DAQmx_Val_Volts, #units for min val and max val
				None) #name of custom scale if used
		except DAQError:
			print("CRITICAL: NO MYDAQ DETECTED, is there a mydaq connected?")
			self.rdy = False
			return
			
		#configurate timing and sample rate for the samples
		self.CfgSampClkTiming(
			"", #source terimal of Sample clock ("" means onboard clock)
			200.0, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #aquire on rising edge of sample clock
			DAQmx_Val_ContSamps, #aquire continues until task stopped
			200) #numb to aquire if finitSamps/ bufferSize if contSamps (bufsize in this case)

class WriteTask(Task):
	def __init__(self):
		Task.__init__(self)
		self.sampswritten = int32()
		self.a = []
		self.rdy = True
		
		#configurate output channel, this is the signal the myDAQ outputs
		try:
			self.CreateAOVoltageChan(
				"myDAQ1/ao0", #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
				"", #name to assign to virt channel mapped to phys channel above
				-10.0, #min value expected to output
				10.0, #max value expected to output
				DAQmx_Val_Volts, #units for min val and max val
				None) #name of custom scale if used
		except DAQError:
			print("CRITICAL: NO MYDAQ DETECTED, is there a mydaq connected?")
			self.rdy = False
			return
		#not configuring sample timing -> driver in on demand sample for anolog out


def feedback(write_end, stop, transferFunct):
	buffer = circularNumpyBuffer(10000, dtype=np.float64) #TODO expose to user (len)
	data = np.empty(100, dtype=np.float64)
	sampsWritten = int32()
	sampsRead = int32()
	
	sendbuf = np.empty(2000)
	start_idx = 0

	t0 = time.time()
	writeTask = WriteTask()
	readTask = ReadTask()
	if(readTask.rdy == False or writeTask.rdy == False):
		print("errors detected, not starting readout!!")
		return 
	
	feedbackSig = np.array([0], dtype=np.float64)#H(buffer.access)
	n= 0
	while(not stop.wait(0)):
		t0
		t1 = time.time()
		#print("latency:",t1-t0)
		readTask.ReadAnalogF64(
			DAQmx_Val_Auto, #read as many samples as there are in the buffer
			0, #timeout in seconds
			DAQmx_Val_GroupByChannel, #read entire channel in one go
			data, #array where the samples should be put in
			100, #number of samples
			byref(sampsRead), #reference where to store: numb of samples read
			None)
		if(sampsRead.value != 0): 
			buffer.append(data[0:sampsRead.value])
			if(n == 200):
				write_end.send(sendbuf[0:start_idx])
				start_idx=0
				n=0
			else:
				sendbuf[start_idx:start_idx+sampsRead.value] = data[0:sampsRead.value]
				start_idx+=sampsRead.value
				n+=1
			
			feedbackSig[0] = np.clip(transferFunct(buffer, feedbackSig[0]), 0, 10)
			#feedbackSig[0] = 1;
			print("feedbacksig:",feedbackSig)
			writeTask.WriteAnalogF64(
				1, #number of samples to write
				True, #start output automatically
				1, #timeout to wait for funct to write samples 
				DAQmx_Val_GroupByChannel, #read entire channel in one go
				feedbackSig, #source array from which to write the data
				byref(sampsWritten),  #variable to store the numb of written samps in
				None)
			t0 = t1
	#shutdown routine
	#start by setting the output signal to zero
	writeTask.StopTask()
	writeTask.WriteAnalogF64(
		1, #number of samples to write
		True, #start output automatically
		1, #timeout to wait for funct to write samples 
		DAQmx_Val_GroupByChannel, #read entire channel in one go
		np.array([0], dtype=np.float64), #source array from which to write the data
		byref(sampsWritten),  #variable to store the numb of written samps in
		None)
	
	readTask.StopTask()
	writeTask.StopTask()
	readTask.ClearTask()
	writeTask.ClearTask()
	print("myDAQ shut down succesfully\n")