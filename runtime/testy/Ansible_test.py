import socket
import threading
#import queue
import time
#import runtime_proto_pb2
import fake_dawn
import random
#import ansible_pb2
data = [0] #for testing purposes
send_port = 1235
recv_port = 1236


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
		return self.data[self.get_index]

processing_cond = threading.RLock()



def unpackage(data):
	return data
	 #need to replace to unpack using protobufs
"""
 dawn_data = ansible_pb2.DawnData()
 try:
 	dawn_data.ParseFromString(data)
 	return dawn_data
 except:
 	return data
"""
def package(state):
	return bytes(state)
	"""
	proto_message = runtime_proto_pb2.RuntimeData()
	proto_message.robot_state = runtime_proto_pb2.RuntimeData.STUDENT_RUNNING
	test_sensor = proto_message.sensor.add()
	test_sensor.id = 'test_sensor'
	test_sensor.type = 'MOTOR_SCALAR'
	test_sensor.value = state[0]
	"""

	return bytes(proto_message.SerializeToString())
###Start Threads###
def package_data(raw_state, packed, lock):
	while(True):
		if (not raw_state is None):
			with lock:
				pack_state = package(raw_state[0])#add actual packaging here
				packed[0]=pack_state #insert other mutable data structure here. Used to make it easier

def buffer_handling(packaged, lock, send_buffer):
	while(True):
		with lock:
			pack_state = packaged[0]
			send_buffer.replace(pack_state)



def sender(port, send_buffer):
	host = socket.gethostname()
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:#DGRAM for UDP sockets
		i = 0
		while(True):
			msg = send_buffer.get()
			try:
				s.sendto(msg, (host, send_port))
			except:
				pass#can be changed to alerting the main python process

def receiver(port, receive_queue):
	#same thing as the client side from python docs
	host = socket.gethostname()
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #DGRAM for UDP sockets
	#need to receive data
	#will be implemented after proof of concept
	s.bind((host, port))
	while(True):
		data = s.recv(2048)
		unpackaged_data = unpackage(data)
		recv_queue[0]=unpackaged_data

recv_queue = [[0]]

send_buffer = two_buffer(processing_cond)
raw_fake_data = [[0]]
packed_fake_data = [[0]]
dawn_buffer = [0]


pack_thread = threading.Thread(target=package_data, name = "Ansible_packager", args=(raw_fake_data, packed_fake_data, processing_cond))
buffer_thread = threading.Thread(target=buffer_handling, name = "buffer_handler", args=(packed_fake_data, processing_cond, send_buffer))
send_thread = threading.Thread(target=sender, name = "ansible_sender", args=(send_port, send_buffer))
recv_thread = threading.Thread(target=receiver, name = "ansible_receiver", args=(recv_port,  recv_queue))
dawn_send_thread = threading.Thread(target=fake_dawn.sender, name = "dawn_sender", args=(recv_port, dawn_buffer))
dawn_recv_thread = threading.Thread(target=fake_dawn.receiver, name = "dawn_receiver", args=(send_port, dawn_buffer))
send_thread.daemon = True
recv_thread.daemon = True
pack_thread.daemon = True
buffer_thread.daemon = True
dawn_send_thread.daemon = True
dawn_recv_thread.daemon = True
pack_thread.start()
buffer_thread.start()
send_thread.start()
recv_thread.start()
dawn_recv_thread.start()
dawn_send_thread.start() 
counter = 0
while(True):
	raw_fake_data[0]=[counter]
	print("sent to dawn: "+ str(counter))
	print("received from dawn:" + str(recv_queue))
	counter += 1
	if(counter == 256):
		counter = 0
	time.sleep(1)



