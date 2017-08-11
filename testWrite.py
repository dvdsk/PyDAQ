from PyDAQmx import Task
from PyDAQmx.DAQmxConstants import *
from PyDAQmx.DAQmxTypes import *
import numpy as np


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
			1000) #numb to generate if finitSamps/ bufferSize if contSamps (bufsize in this case)
		
		self.WriteAnalogF64(100, 0, DAQmx_Val_WaitInfinitely, DAQmx_Val_GroupByChannel, self.outputData, byref(self.sampswritten), None);

if __name__ == "__main__":
	outputShape = np.sin(np.linspace(0, np.pi, num =100, endpoint=False))
	
	print(outputShape)
	
	task=WriteCallbackTask(outputShape)
	task.StartTask()

	input('Acquiring samples continuously. Press Enter to interrupt\n')

	task.StopTask()
	task.ClearTask()