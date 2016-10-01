import socket
import threading
import queue
import time
data = [0]
send_port = 1236
recv_port = 1235

def sender(port, send_queue):
	host = socket.gethostname()
	with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:#DGRAM for UDP sockets
		while(True):
			msg = None
			msg = bytes(send_queue[0])
			#msg = bytes([5])
			s.sendto(msg, (host, send_port))
def receiver(port, receive_queue):
	#same thing as the client side from python docs
	host = socket.gethostname()
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #DGRAM for UDP sockets
	#need to receive data
	s.bind((host, recv_port))
	while(True):
		#would actuall be:
		msg, addr = s.recvfrom(2048)
		receive_queue[0]=msg

#write tests
