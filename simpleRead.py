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

class ReadCallbackTask(Task):
	def __init__(self, inputChannels, samplerate, maxMeasures, minMeasures):
		Task.__init__(self)
		# self.data = np.empty(samplerate*len(inputChannels),dtype=np.float64)
		self.data = np.full(samplerate*len(inputChannels), 0,dtype=np.float64)
		self.a = []
		self.rdy = True
		self.samplerate = samplerate
		for inputChannel, maxMeasure, minMeasure in zip(inputChannels, maxMeasures, minMeasures):
			try:
				#configurate input channel, where we read the ouput from the myDAQ
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
		self.AutoRegisterEveryNSamplesEvent(
			DAQmx_Val_Acquired_Into_Buffer, #the event on which the callback task starts
			samplerate, #number of samples after which event should occur
			0) #process callback funct in daqmx thread (alternative DAQmx_Val_SynchronousEventCallbacks)
		self.AutoRegisterDoneEvent(0)
		
	def DoneCallback(self, status):
		print("Status"),status.value
		return 0 # The function should return an integer

class ReadToOnePipe(ReadCallbackTask):
	def __init__(self, write_end, inputChannel, samplerate, maxMeasure, minMeasure):
		print(inputChannel, samplerate, maxMeasure, minMeasure)
		ReadCallbackTask.__init__(self, inputChannel, samplerate, maxMeasure, minMeasure)
		self.write_end = write_end #transport pipe to other process
		self.nChannels = len(inputChannel)
	def EveryNCallback(self):
		read = int32()
		self.ReadAnalogF64(
			self.samplerate, #number of samples to read per channel
			10.0, #timeout in seconds
			DAQmx_Val_GroupByScanNumber, #read first sample of every channel then second etc
			self.data, #array where the samples should be put in
			len(self.data), #number of samples we can store
			byref(read), #reference where to store: numb of samples read
			None)
		self.a.extend(self.data.tolist())
		tosend = self.data.reshape((self.nChannels, len(self.data)/self.nChannels))
		self.write_end.send(tosend)
		return 0 # The function should return an integer

class ReadToTwoPipes(ReadCallbackTask):
	def __init__(self, write_end1, write_end2, inputChannel, samplerate, maxMeasure, minMeasure):
		ReadCallbackTask.__init__(self, inputChannel, samplerate, maxMeasure, minMeasure)
		self.nChannels = len(inputChannel)
		self.write_end1 = write_end1 #transport pipe to other process
		self.write_end2 = write_end2 #transport pipe to other process
	def EveryNCallback(self):
		read = int32()
		self.ReadAnalogF64(
			self.samplerate, #number of samples to read per channel
			10.0, #timeout in seconds
			DAQmx_Val_GroupByScanNumber, #read first sample of every channel then second etc
			self.data, #array where the samples should be put in
			len(self.data), #number of samples we can store
			byref(read), #reference where to store: numb of samples read
			None)
		self.a.extend(self.data.tolist())
		tosend = self.data.reshape((len(self.data)//self.nChannels, self.nChannels))
		self.write_end1.send(tosend)
		self.write_end2.send(tosend)
		return 0 # The function should return an integer

class WriteTask(Task):
	def __init__(self, outputChannels, outputData, samplerate, maxMeasure, minMeasure):
		Task.__init__(self)
		self.sampswritten = int32()
		self.a = []
		self.rdy = True
		for outputChannel, maxMeasure, minMeasure in zip(outputChannels, maxMeasure, minMeasure):
			try:
				#configurate output channel, this is the signal the myDAQ outputs
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
		
		#configurate timing and sample rate for the samples
		self.CfgSampClkTiming(
			"", #source terimal of Sample clock ("" means onboard clock)
			samplerate, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #generage on rising edge of sample clock
			DAQmx_Val_ContSamps, #generate continues until task stopped
			len(outputData)) #numb to generate if finitSamps/ bufferSize if contSamps (bufsize in this case)
		self.WriteAnalogF64(
			len(outputData)//len(outputChannels), #number of samples to write
			False, #start output automatically
			DAQmx_Val_WaitInfinitely, #timeout to wait for funct to write samples 
			DAQmx_Val_GroupByChannel, #read entire channel in one go
			outputData, #source array from which to write the data
			byref(self.sampswritten), #variable to store the numb of written samps in
			None)

def startReadOnly(input_write_ends, stop, rdy,
	              inputChannel, samplerate, maxMeasure, minMeasure):
	sampswritten = int32()
	
	if(len(input_write_ends) == 1):
		readInTask= ReadToOnePipe(input_write_ends[0], inputChannel, samplerate, maxMeasure, minMeasure)
	else: #its 2
		readInTask= ReadToTwoPipes(input_write_ends[0], input_write_ends[1], inputChannel, samplerate, maxMeasure, minMeasure)

	if(readInTask.rdy == False):
		print("errors detected, not starting readout!!")
		return 

	readInTask.StartTask()
	rdy.set()
	stop.wait()

	#shutdown routine
	readInTask.StopTask()
	readInTask.ClearTask()
	if(isinstance(inputChannel, list)):
		print(", ".join(inputChannel, )+": closed")
	else:
		print(inputChannel+": closed")

def startGenOnly(output_read_end, stop, rdy, outputChannels,
				 outputShape, samplerate, maxMeasure, minMeasure):

	sampswritten = int32()
	writeInTask=WriteTask(outputChannels, outputShape, samplerate, maxMeasure, minMeasure)
	if(writeInTask.rdy == False):
		print("errors detected, not starting generation!!")
		return 

	writeInTask.StartTask()
	print("started gen")
	rdy.set()
	
	#every second check if the output should change
	while(not stop.wait(1)):
		if(output_read_end.poll()):
			print("updating output waveform")
			outputData = output_read_end.recv() #for 2 channels supply 2*200 
			print(outputData)
			writeInTask.StopTask()
			writeInTask.WriteAnalogF64(
				len(outputData)/len(outputChannels), #number of samples to write
				True, #start output automatically
				DAQmx_Val_WaitInfinitely, #timeout to wait for funct to write samples 
				DAQmx_Val_GroupByChannel, #write entire channel in one go
				outputData, #source array from which to write the data
				byref(sampswritten), #variable to store the numb of written samps in
				None)
		else:
			continue

	#shutdown routine
	#start by setting the output signal to zero
	writeInTask.StopTask()
	writeInTask.WriteAnalogF64(
		2, #number of samples to write
		True, #start output automatically
		1, #timeout to wait for funct to write samples 
		DAQmx_Val_GroupByChannel, #write entire channel in one go
		np.array([0,0], dtype=np.float64), #source array from which to write the data
		byref(sampswritten),  #variable to store the numb of written samps in
		None)

	writeInTask.StopTask()
	writeInTask.ClearTask()
	if(isinstance(outputChannels, list)):
		print(", ".join(outputChannels, )+": closed and reset to 0 volt")
	else:
		print(outputChannels+": closed and reset to 0 volt")

def startReadAndGen(input_write_ends, output_read_end, stop, rdy, outputChannels,
	                outputShape, inputChannel, samplerate, maxMeasure, minMeasure):
	sampswritten = int32()
	if(len(input_write_ends) == 1):
		readInTask= ReadToOnePipe(input_write_ends[0], inputChannel, samplerate, maxMeasure[0], minMeasure[0])
	else: #its 2
		readInTask= ReadToTwoPipes(input_write_ends[0], input_write_ends[1], inputChannel, samplerate, maxMeasure[0], minMeasure[0])
		
	writeInTask=WriteTask(outputChannels, outputShape, samplerate, maxMeasure[1], minMeasure[1])
	
	if(readInTask.rdy == False or writeInTask.rdy == False):
		print("errors detected, not starting generation nor readout!!")
		return 

	readInTask.StartTask()
	writeInTask.StartTask()
	rdy.set()
	
	#every second check if the output should change
	while(not stop.wait(1)):
		if(output_read_end.poll()):
			print("updating output waveform")
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
	#start by setting the output signal to zero
	writeInTask.StopTask()
	writeInTask.WriteAnalogF64(
		2, #number of samples to write
		True, #start output automatically
		1, #timeout to wait for funct to write samples 
		DAQmx_Val_GroupByScanNumber, #read first sample of every channel then second etc
		np.array([0,0], dtype=np.float64), #source array from which to write the data
		byref(sampswritten),  #variable to store the numb of written samps in
		None)

	readInTask.StopTask()
	writeInTask.StopTask()
	readInTask.ClearTask()
	writeInTask.ClearTask()
	
	if(isinstance(outputChannels, list)):
		outChannString = ", ".join(outputChannels)
	else:
		outChannString = outputChannels
	if(isinstance(inputChannel, list)):
		inputChannString = ", ".join(inputChannel)
	else:
		inputChannString = inputChannel
	print(inputChannString+": closed, "+outChannString+": closed and reset to 0 volt")