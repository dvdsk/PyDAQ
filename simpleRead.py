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

class CallbackTask(Task):
    def __init__(self):
        Task.__init__(self)
        self.data = np.zeros(1000)
        self.a = []
        self.CreateAIVoltageChan(
			"myDAQ1/ai0", #The name of the physical channel muDAQ1/aiN  (n= 0 or 1)
			"", #name to assign to virt channel mapped to phys channel above
			DAQmx_Val_Cfg_Default, #measurement technique used
			-10.0, #min value expected to measure
			10.0, #max value expected to measure
			DAQmx_Val_Volts, #scale for above units
			None) #name of custom scale if used
        self.CfgSampClkTiming(
			"", #source terimal of Sample clock ("" means onboard clock)
			10000.0, #sample rate (units: samples/second/channel)
			DAQmx_Val_Rising, #aquire on rising edge of sample clock
			DAQmx_Val_ContSamps, #aquire continues until task stopped
			1000) #numb to aquire if finitSamps
        self.AutoRegisterEveryNSamplesEvent(
			DAQmx_Val_Acquired_Into_Buffer, #when the event (callback task) happens
			1000,0) #number of samples after which event should occur
        self.AutoRegisterDoneEvent(0)
    def EveryNCallback(self):
        read = int32()
        self.ReadAnalogF64(
			1000, #number of samples to read
			10.0, #timeout in seconds
			DAQmx_Val_GroupByChannel, #read entire channel in one go
			self.data, #array where the samples should be put in
			1000, #number of samples 
			byref(read), #reference where to store: numb of samples read
			None)
        self.a.extend(self.data.tolist())
        print(self.data[0])
        return 0 # The function should return an integer
    def DoneCallback(self, status):
        print("Status"),status.value
        return 0 # The function should return an integer


task=CallbackTask()
task.StartTask()

input('Acquiring samples continuously. Press Enter to interrupt\n')

task.StopTask()
task.ClearTask()