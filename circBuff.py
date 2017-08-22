import numpy as np

class circularNumpyBuffer:
	"""A numpy implementation of a circular buffer, a circular buffer can append data forever
	   but starts overwriting old data after its capacity is reached. It thus only remembers the
	   last data. This simple implementation has no check on the appending data, make sure
	   it is not larger then the capacity of this buffer. It is only capable of appending numpy arrays
	   not other data.
	"""
	def __init__(self, capacity, dtype=np.float64):
		#internal buffer is 10x larger to minimise the amount of move operations needed
		self.arrLen = capacity*10
		self.arr = np.empty(self.arrLen, dtype)

		#indexes used to keep track of where the current data is
		self.left_index = 0
		self.right_index = 0
		self.capacity = capacity
	def append(self,sample):
		#check if we have enough space left in the array
		if(self.right_index+len(sample)<self.arrLen):
			#copy the new data into the array
			usedCapacity = self.right_index-self.left_index
			self.arr[self.right_index : self.right_index+len(sample)] = sample
			#check if we are at capacity and need to 'forget' some data by shifting the left index
			if(usedCapacity + len(sample) > self.capacity):
				self.left_index += len(sample)
			self.right_index += len(sample)
		else:
			#start by forgetting the data we no longer need
			newLeft = self.left_index+np.size(sample)
			#copy the data from the end of the array to the start so we have enough space again
			self.arr[0:(self.right_index - newLeft)] = self.arr[newLeft:self.right_index]
			#update indexes reflecting we now start at the beginning of the array
			self.right_index = self.right_index - newLeft
			self.left_index = 0
			#store sample and update right index 
			#left index does not need updating as we started by updating left/forgetting some data
			#and took this into account when moving data back to the the start of the array
			self.arr[self.right_index : self.right_index+len(sample)] = sample
			self.right_index += len(sample)
	def access(self):
		#print(self.left_index)
		#print(self.right_index)
		return self.arr[self.left_index : self.right_index]
	def __len__(self):
		return self.right_index-self.left_index