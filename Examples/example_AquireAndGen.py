if __name__ == '__main__':
	import pyMyDAQ as pd
	import numpy as np

	pd = pd.PyDAQ()

	#configure
	pd.setFileOptions(name="testData", format="csv")
	pd.aquireAndGen(["myDAQ1/ai0","myDAQ1/ai1"],"myDAQ1/ao0",np.arange(-5,5),samplerate=100)

	pd.begin()
	pd.menu()
	pd.end()
	
	while(pd.Running){
		
	
	
	
	}