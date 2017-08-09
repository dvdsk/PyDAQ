import multiprocessing as mp
import time #TODO DEBUG ONLY

import simpleRead
import plotThread



if __name__ == "__main__":
	stop = mp.Event()
	write_end, read_end = mp.Pipe()
	
	plotting = mp.Process(target = plotThread.testPipes, args = (read_end,stop,))
	aquisition = mp.Process(target = simpleRead.startCallBack, args = (write_end,stop,))

	plotting.start()
	aquisition.start()
	
	time.sleep(2)
	input('Acquiring samples continuously. Press Enter to interrupt\n')
	stop.set()
	
	plotting.join()
	aquisition.join()