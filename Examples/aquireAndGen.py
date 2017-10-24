import pydaq
import numpy as np

if __name__ == '__main__':

	outputChannel1 = np.sin(np.linspace(0, 2*np.pi, num =1000,
	                 endpoint=False, dtype=np.float64))
	outputChannel2 = np.cos(np.linspace(0, 2*np.pi, num =1000, 
	                 endpoint=False, dtype=np.float64))
	outputPattern = outputChannel1 + outputChannel2


	pd = pydaq.PyDAQ()

	#configure
	pd.setFileOptions(name="testData", format="csv")
	pd.aquireAndGen(["myDAQ1/ai0","myDAQ1/ai1"],
	                ["myDAQ1/ao0", "myDAQ1/ao1"],
	                outputChannel1,samplerate=100)

	pd.begin()
	pd.menu()
	pd.end()