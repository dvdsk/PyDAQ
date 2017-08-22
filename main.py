import multiprocessing as mp
import numpy as np
import time #TODO DEBUG ONLY


import simpleRead
import feedback
import plotThread


if __name__ == "__main__":
	stop = mp.Event()
	rdy = mp.Event()
	input_write_end, input_read_end = mp.Pipe()
	output_write_end, output_read_end = mp.Pipe()
	outputShape = np.sin(np.linspace(0, 2*np.pi, num =200, endpoint=False, dtype=np.double))
	
	plotting_thread = mp.Process(target = plotThread.testPipes, args = (input_read_end, stop, outputShape,))
	#aquisition = mp.Process(target = simpleRead.startCallBack, args = (input_write_end, output_read_end, stop,outputShape,))
	feedback_thread = mp.Process(target = feedback.feedback, args = (input_write_end, stop,rdy,))

	

	#aquisition.start()
	plotting_thread.start()
	feedback_thread.start()
	
	rdy.wait()
	
	#outputShape = np.linspace(5,5, num =200, endpoint=False, dtype=np.double)
	#output_write_end.send(outputShape)
	
	input('Acquiring samples continuously. Press Enter to interrupt\n')
	stop.set()
	
	plotting_thread.join()
	#aquisition.join()
	feedback_thread.join()