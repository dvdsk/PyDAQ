import pyMyDAQ as pd

import numpy as np



#een feedback funct
def transferFunct(buffer, feedbackSig):
	V = buffer.access()[-1]
	R = V/((5-V)/1000)
	print("V: ",V,"R: ",R)
	if(R > 822.5):
		feedbackSig += 0.1
	else:
		feedbackSig -= 0.1
	print("feedbackSig:",feedbackSig)
	return feedbackSig

outputShape = np.sin(np.linspace(0, 2*np.pi, num =200, endpoint=False, dtype=np.double))

if __name__ == '__main__':
	pd = pd.PyDAQ()
	pd.plot()
	# # pd.Feedback()
	pd.aquisition(outputShape)

	pd.begin()
	pd.menu()
	pd.end()