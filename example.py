import pyMyDAQ as pd
import numpy as np



#een feedback funct
def transferFunct(buffer, feedbackSig):
	V = buffer.access()[-1]
	R = V/((5-V)/1000)
	# print("V: ",V,"R: ",R)
	if(R > 822.5):
		feedbackSig += 0.1
	else:
		feedbackSig -= 0.1
	# print("feedbackSig:",feedbackSig)
	return feedbackSig

outputShape = np.sin(np.linspace(0, 2*np.pi, num =2000, endpoint=False, dtype=np.float64))

"myDAQ1/ao0"
"myDAQ1/ai0"

if __name__ == '__main__':
	pd = pd.PyDAQ()
	
	pd.onlyFeedback(["myDAQ1/ai1", "myDAQ1/ao1"], transferFunct)
	#pd.onlyGen(["myDAQ1/ao1", "myDAQ1/ao0"], outputShape)
	#pd.onlyAquire("myDAQ1/ai1", maxMeasure=2)
	#pd.aquireAndGen("myDAQ1/ai1", "myDAQ1/ao1", outputShape)

	
	pd.begin()
	pd.menu()
	pd.end()