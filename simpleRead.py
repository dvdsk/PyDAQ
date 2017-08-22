import multiprocessing as mp

from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxTypes import *
from PyDAQmx.DAQmxFunctions import DAQError
import numpy as np
import time


"""
See documentation at: http://zone.ni.com/reference/en-XX/help/370471AA-01/

-Constants are imported from PyDAQmx.DAQmxConstants

-Variables that are not pointers can be used directly,
as they will be automatically converted by ctypes

-For pointers, first declare them and then use byref() 
to pass by referenceNULL in C becomes None in Python
"""


import os
import sys
import textwrap
import numpy as np
from numpy import ctypeslib
import ctypes
import ctypes.util
import warnings

#def checkMyDAQConnection():


class ReadCallbackTask(Task):
	def __init__(self, write_end):
		Task.__init__(self)
		self.write_end = write_end #transport pipe to other process
		self.data = np.empty(2000)
		self.a = []
		self.rdy = True
		
		try:
			#configurate input channel, where we read the ouput from the myDAQ
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
			2000.0, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #aquire on rising edge of sample clock
			DAQmx_Val_ContSamps, #aquire continues until task stopped
			2000) #numb to aquire if finitSamps/ bufferSize if contSamps (bufsize in this case)
		self.AutoRegisterEveryNSamplesEvent(
			DAQmx_Val_Acquired_Into_Buffer, #the event on which the callback task starts
			2000,0) #number of samples after which event should occur
		self.AutoRegisterDoneEvent(0)
		
	def EveryNCallback(self):
		read = int32()
		self.ReadAnalogF64(
			2000, #number of samples to read
			10.0, #timeout in seconds
			DAQmx_Val_GroupByChannel, #read entire channel in one go
			self.data, #array where the samples should be put in
			2000, #number of samples 
			byref(read), #reference where to store: numb of samples read
			None)
		self.a.extend(self.data.tolist())
		#print(self.data[0])
		self.write_end.send(self.data)
		return 0 # The function should return an integer
	def DoneCallback(self, status):
		print("Status"),status.value
		return 0 # The function should return an integer

class WriteTask(Task):
	def __init__(self, outputData):
		Task.__init__(self)
		self.outputData = outputData
		self.sampswritten = int32()
		self.a = []
		self.rdy = True
		try:
			#configurate output channel, this is the signal the myDAQ outputs
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
		
		#configurate timing and sample rate for the samples
		self.CfgSampClkTiming(
			"", #source terimal of Sample clock ("" means onboard clock)
			200.0, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #generage on rising edge of sample clock
			DAQmx_Val_ContSamps, #generate continues until task stopped
			200) #numb to generate if finitSamps/ bufferSize if contSamps (bufsize in this case)
		self.WriteAnalogF64(
			200, #number of samples to write
			False, #start output automatically
			DAQmx_Val_WaitInfinitely, #timeout to wait for funct to write samples 
			DAQmx_Val_GroupByChannel, #read entire channel in one go
			self.outputData, #source array from which to write the data
			byref(self.sampswritten), #variable to store the numb of written samps in
			None)


def startCallBack(input_write_end, output_read_end, stop, outputShape):
	readInTask=ReadCallbackTask(input_write_end)
	writeInTask=WriteTask(outputShape)
	if(readInTask.rdy == False or writeInTask.rdy == False):
		print("errors detected, not starting readout!!")
		return 
	
	readInTask.StartTask()
	writeInTask.StartTask()
	
	#every second check if the output should change
	while(not stop.wait(1)):
		if(output_read_end.poll()):
			print("updating output waveform")
			sampswritten = int32()
			outputData = output_read_end.recv()
			print(outputData)
			writeInTask.StopTask()
			writeInTask.WriteAnalogF64(
				200, #number of samples to write
				True, #start output automatically
				DAQmx_Val_WaitInfinitely, #timeout to wait for funct to write samples 
				DAQmx_Val_GroupByChannel, #read entire channel in one go
				outputData, #source array from which to write the data
				byref(sampswritten), #variable to store the numb of written samps in
				None)
	#shutdown routine
	readInTask.StopTask()
	writeInTask.StopTask()
	readInTask.ClearTask()
	writeInTask.ClearTask()
	print("myDAQ shut down succesfully\n")