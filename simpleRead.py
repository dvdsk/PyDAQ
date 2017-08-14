import multiprocessing as mp

from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxTypes import *
import numpy as np



"""
See documentation at: http://zone.ni.com/reference/en-XX/help/370471AA-01/

-Constants are imported from PyDAQmx.DAQmxConstants

-Variables that are not pointers can be used directly,
as they will be automatically converted by ctypes

-For pointers, first declare them and then use byref() 
to pass by referenceNULL in C becomes None in Python
"""

class ReadCallbackTask(Task):
	def __init__(self, write_end):
		Task.__init__(self)
		self.write_end = write_end #transport pipe to other process
		self.data = np.empty(2000)
		self.a = []
		
		#configurate input channel, where we read the ouput from the myDAQ
		self.CreateAIVoltageChan(
			"myDAQ1/ai0", #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
			"", #name to assign to virt channel mapped to phys channel above
			DAQmx_Val_Cfg_Default, #measurement technique used
			-10.0, #min value expected to measure
			10.0, #max value expected to measure
			DAQmx_Val_Volts, #units for min val and max val
			None) #name of custom scale if used

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

class WriteCallbackTask(Task):
	def __init__(self, outputData):
		Task.__init__(self)
		self.outputData = outputData
		self.sampswritten = int32()
		self.a = []

		#configurate output channel, this is the signal the myDAQ outputs
		self.CreateAOVoltageChan(
			"myDAQ1/ao0", #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
			"", #name to assign to virt channel mapped to phys channel above
			-10.0, #min value expected to output
			10.0, #max value expected to output
			DAQmx_Val_Volts, #units for min val and max val
			None) #name of custom scale if used

		#configurate timing and sample rate for the samples
		self.CfgSampClkTiming(
			"", #source terimal of Sample clock ("" means onboard clock)
			200.0, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #generage on rising edge of sample clock
			DAQmx_Val_ContSamps, #generate continues until task stopped
			200) #numb to generate if finitSamps/ bufferSize if contSamps (bufsize in this case)
		
		self.WriteAnalogF64(200, 0, DAQmx_Val_WaitInfinitely, DAQmx_Val_GroupByChannel, self.outputData, byref(self.sampswritten), None);

def startCallBack(write_end, stop, outputShape):
	print("starting stuff")
	readInTask=ReadCallbackTask(write_end)
	writeInTask=WriteCallbackTask(outputShape)
	
	readInTask.StartTask()
	writeInTask.StartTask()
	
	stop.wait()
	print("shutting down myDAQ\n")

	readInTask.StopTask()
	writeInTask.StopTask()
	readInTask.ClearTask()
	writeInTask.ClearTask()
	print("startCallBack rdy to join")

if __name__ == "__main__":
	write_end, read_end = mp.Pipe()
	startCallBack(write_end)
	#input('Acquiring samples continuously. Press Enter to interrupt\n')
	
	# task=CallbackTask(write_end)
	# task.StartTask()

	# input('Acquiring samples continuously. Press Enter to interrupt\n')

	# task.StopTask()
	# task.ClearTask()