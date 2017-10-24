import pydaq
import numpy as np

if __name__ == '__main__':

	outputChannel1 = np.full(1000, 2, dtype=np.float64)
	outputChannel2 = np.full(1000, 1, dtype=np.float64)
	outputPattern = np.hstack((outputChannel1,outputChannel2))
	
	pd = pydaq.PyDAQ()

	#configure
	pd.setFileOptions(name="testData", format="csv")
	pd.aquireAndGen(["myDAQ1/ai0","myDAQ1/ai1"],["myDAQ1/ao0","myDAQ1/ao1"],outputPattern,samplerate=100)

	pd.begin()
	pd.menu()
	pd.end()