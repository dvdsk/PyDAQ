import pyMyDAQ as pd
import numpy as np
#import yappi #Used for profiling code


#een feedback funct
def transferFunct(buffer, feedbackSig):
	lenEven = len(buffer)//2*2
	V = buffer.access()[lenEven-2]
	R = V/((5-V)/1000)
	if(R > 822.5):
		feedbackSig[0] += 0.1
	else:
		feedbackSig[0] += 0.1
	
	feedbackSig[0] = 10
	feedbackSig[1] = 10
	feedbackSig = np.clip(feedbackSig, -10, 10)
	return feedbackSig

outputShape = np.sin(np.linspace(0, 2*np.pi, num =2000, endpoint=False, dtype=np.float64))

if __name__ == '__main__':
#yappi.start()
	
	pd = pd.PyDAQ()
	
	pd.onlyFeedback(["myDAQ1/ai1", "myDAQ1/ai0"],["myDAQ1/ao1", "myDAQ1/ao0"], transferFunct)
	#pd.onlyGen(["myDAQ1/ao1", "myDAQ1/ao0"], outputShape)
	#pd.onlyAquire("myDAQ1/ai1", maxMeasure=2)
	#pd.aquireAndGen("myDAQ1/ai1", "myDAQ1/ao1", outputShape)

	
	pd.begin()
	pd.menu()
	pd.end()
	
#yappi.stop()
#print(yappi.get_func_stats() )