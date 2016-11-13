import socket
import threading
import queue
import time
import runtime_pb2
import ansible_pb2

data = [0]
send_port = 1236
recv_port = 1235
dawn_hz = 10

def dawn_packager(data):
    proto_message = ansible_pb2.DawnData()
    proto_message.student_code_status = 1
    test_gamepad = proto_message.gamepads.add() 
    test_gamepad.index = 0
    test_gamepad.axes.append(.5)
    test_gamepad.buttons.append(True)
    return proto_message.SerializeToString()

def sender(port, send_queue):
    host = '127.0.0.1'
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        while True:
            next_call = time.time()
            msg = None
            msg = dawn_packager(0)
            s.sendto(msg, (host, send_port))
            next_call += 1.0/dawn_hz
            if next_call > time.time():
                time.sleep(next_call - time.time())

def receiver(port, receive_queue):
    host = '127.0.0.1'
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host, recv_port))
    while True:
        msg, addr = s.recvfrom(2048)
        runtime_message = runtime_pb2.RuntimeData()
        runtime_message.ParseFromString(msg)
        print(runtime_message.robot_state)
        for sensor in runtime_message.sensor_data:
            print(sensor.device_type)
            print(sensor.device_name)
            print(sensor.value)
            print(sensor.uid)
        receive_queue[0]=msg

sender_thread = threading.Thread(target = sender, name = "fake dawn sender", args = (send_port, data))
recv_thread = threading.Thread(target = receiver, name = "fake dawn receiver", args = (recv_port, data))
sender_thread.daemon = True
recv_thread.daemon = True
recv_thread.start()
sender_thread.start()

#Just Here for testing, should not be run regularly
while True:
    time.sleep(1)
