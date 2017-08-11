import multiprocessing as mp
import numpy as np
import time #TODO DEBUG ONLY


import simpleRead
import plotThread



if __name__ == "__main__":
	stop = mp.Event()
	write_end, read_end = mp.Pipe()
	outputShape = np.sin(np.linspace(0, np.pi, num =1000, endpoint=False, dtype=np.double))
	
	plotting = mp.Process(target = plotThread.testPipes, args = (read_end,stop,))
	aquisition = mp.Process(target = simpleRead.startCallBack, args = (write_end,stop,outputShape,))

	plotting.start()
	aquisition.start()
	
	time.sleep(2)
	input('Acquiring samples continuously. Press Enter to interrupt\n')
	stop.set()
	
	plotting.join()
	aquisition.join()