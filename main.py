import multiprocessing as mp
import numpy as np
import time #TODO DEBUG ONLY


import simpleRead
import feedback
import plotThread


#een feedback funct
def transferFunct(buffer, feedbackSig):
	V = buffer.access()[-1]
	R = V/((5-V)/1000)
	print("V: ",V,"R: ",R)
	if(R > 822.5):
		feedbackSig += 0.1
	else:
		feedbackSig -= 0.1
	print("feedbackSig:",feedbackSig)
	return feedbackSig

if __name__ == "__main__":
	stop = mp.Event()
	rdy = mp.Event()
	input_write_end, input_read_end = mp.Pipe()
	output_write_end, output_read_end = mp.Pipe()
	outputShape = np.sin(np.linspace(0, 2*np.pi, num =200, endpoint=False, dtype=np.double))
	
	plotting_thread = mp.Process(target = plotThread.testPipes, args = (input_read_end, stop, outputShape,rdy,))
	#aquisition = mp.Process(target = simpleRead.startCallBack, args = (input_write_end, output_read_end, stop,outputShape,))
	
	
	feedback_thread = mp.Process(target = feedback.feedback, args = (input_write_end, stop,))

	

	#aquisition.start()
	plotting_thread.start()
	feedback_thread.start()
	
	rdy.wait()
	#time.sleep(5)
	
	#outputShape = np.linspace(5,5, num =200, endpoint=False, dtype=np.double)
	#output_write_end.send(outputShape)
	
	input('Acquiring samples continuously. Press Enter to interrupt\n')
	print("test test")
	stop.set()
	
	plotting_thread.join()
	#aquisition.join()
	feedback_thread.join()