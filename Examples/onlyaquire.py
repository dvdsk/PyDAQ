import pydaqmx
import numpy as np

if __name__ == '__main__':

	pd = pydaqmx.PyDAQ()

	#configure
	pd.onlyAquire(["myDAQ1/ai0", "myDAQ1/ai1"], 
	  samplerate=800, maxMeasure=2, minMeasure=-2,
	  plot=True, saveData=True)

	pd.begin()
	pd.menu()
	pd.end()