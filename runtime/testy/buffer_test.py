import socket
import threading
import queue
import time
class two_buffer():
	def __init__(self, condition):
		self.data = [None, None]
		self.condition = condition
		self.put_index = 0
		self.get_index = 1
	def replace(self, item):
		self.data[self.put_index] = item
		self.put_index = (self.put_index + 1) % 2
		self.get_index = (self.get_index + 1) % 2
	def get(self):
		print(self.get_index)
		return self.data[self.get_index]
	def __str__(self):
		return str(self.data)

processing_cond = threading.RLock()



def unpackage(data):
	return data #need to replace to unpack using protobufs

def package_data(raw_state, packed, lock):
	while(True):
		if (not raw_state is None):
			with lock:
				pack_state = unpackage(raw_state)#add actual packaging here
				packed[0]=pack_state #insert other mutable data structure here. Used to make it easier
def buffer_handling(packaged, lock, send_buffer):
	while(True):
		with lock:
			pack_state = packaged[0]
			send_buffer.replace(pack_state)
		

send_buffer = two_buffer(processing_cond)
raw_fake_data = [[0]]
packed_fake_data = [[0]]
pack_thread = threading.Thread(target=package_data, name = "Ansible_packager", args=(raw_fake_data, packed_fake_data, processing_cond))
buffer_thread = threading.Thread(target=buffer_handling, name = "buffer_handler", args=(packed_fake_data, processing_cond, send_buffer))
pack_thread.daemon = True
buffer_thread.daemon = True
pack_thread.start()
buffer_thread.start()

#test one
for i in range(10):
	raw_fake_data[0]=[raw_fake_data[0][0]+1]
	print(send_buffer)
	time.sleep(.1)
assert send_buffer.data==[[[10]],[[10]]], "initial test" 
print("passed test one")
