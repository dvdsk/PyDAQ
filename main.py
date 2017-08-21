import multiprocessing as mp
import numpy as np
import time #TODO DEBUG ONLY


import simpleRead
import feedback
import plotThread

"""
Process Process-1:
Traceback (most recent call last):
  File "C:\Anaconda3\lib\multiprocessing\process.py", line 249, in _bootstrap
    self.run()
  File "C:\Anaconda3\lib\multiprocessing\process.py", line 93, in run
    self._target(*self._args, **self._kwargs)
  File "P:\PyDAQ\plotThread.py", line 81, in testPipes
    buffer.append(data)
  File "P:\PyDAQ\plotThread.py", line 46, in append
    self.arr[self.right_index : np.size(sample)] = sample
ValueError: could not broadcast input array from shape (2000) into shape (0)
"""


if __name__ == "__main__":
	stop = mp.Event()
	input_write_end, input_read_end = mp.Pipe()
	output_write_end, output_read_end = mp.Pipe()
	outputShape = np.sin(np.linspace(0, 2*np.pi, num =200, endpoint=False, dtype=np.double))
	
	plotting = mp.Process(target = plotThread.testPipes, args = (input_read_end, stop, outputShape,))
	aquisition = mp.Process(target = simpleRead.startCallBack, args = (input_write_end, output_read_end, stop,outputShape,))
	#feedback = mp.Process(target = feedback.feedback, args = (write_end,stop,))

	
	plotting.start()
	aquisition.start()
	#feedback.start()
	
	time.sleep(5)
	
	outputShape = np.sin(np.linspace(0, np.pi, num =200, endpoint=False, dtype=np.double))
	output_write_end.send(outputShape)
	
	input('Acquiring samples continuously. Press Enter to interrupt\n')
	stop.set()
	
	plotting.join()
	aquisition.join()
	#feedback.join()