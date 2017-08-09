import multiprocessing as mp

def testPipes(read_end, stop):
	while(not stop.is_set()):
		print("reading from pipe")
		result = read_end.recv()
		print("result: ")
		print(result[0])