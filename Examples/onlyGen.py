import pydaqmx
import numpy as np

if __name__ == '__main__':

	outputChannel1 = np.sin(np.linspace(0, 2*np.pi, num =1000,
	                 endpoint=False))
	outputChannel2 = np.cos(np.linspace(0, 2*np.pi, num =1000,
	                 endpoint=False))
	outputPattern = outputChannel1 + outputChannel2 

	pd = pydaqmx.PyDAQ()

	#configure
	pd.onlyGen(["myDAQ1/ao0", "myDAQ1/ao1"], outputPattern,
	   samplerate=1000, maxGen=10, minGen=-10)
	   
	pd.begin()
	pd.menu()
	pd.end()