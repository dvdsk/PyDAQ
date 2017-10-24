import pydaq
import numpy as np

def transferFunct(buffer, feedbackSig):
	lenEven = len(buffer)//2*2
	V = buffer.access()[lenEven-2]
	R = V/((5-V)/1000)
	if(R > 822.5):
		feedbackSig[0] += 0.1
	else:
		feedbackSig[0] += 0.1
	
	feedbackSig = np.clip(feedbackSig, -10, 10)
	return feedbackSig

if __name__ == '__main__':
	pd = pydaq.PyDAQ()

	#configure
	pd.setFileOptions(name="testData", format="csv")
	pd.onlyFeedback("myDAQ1/ai0","myDAQ1/ao0",transferFunct,samplerate=100)

	
	pd.begin()
	pd.menu()
	pd.end()