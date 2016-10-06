import socket
import threading
import time
import fake_dawn
import random
import sys
from runtimeUtil import *

class TwoBuffer(): 
    """Custom buffer class for handling states.

    Holds two states, one which is updated and one that is sent. 

    """
    
    def __init__(self):
        self.data = [0, 0]
        self.put_index = 0
        self.get_index = 1

    def replace(self, item):
        self.data[self.put_index] = item
        self.put_index = 1 - self.put_index
        self.get_index = 1 - self.get_index

    def get(self):
        return self.data[self.get_index]

class AnsibleHandler():
    def __init__(self, packagerName, socketName, packager, socketThread, badThingsQueue, stateQueue, pipe):
        self.packagerFunc = packager
        self.socketFunc = socketThread
        self.badThingsQueue = badThingsQueue
        self.stateQueue = stateQueue
        self.pipe = pipe
        self.packagerName = packagerName
        self.socketName = socketName

    def threadMaker(self, threadTarget, threadName):
        thread = threading.Thread(target = threadTarget, name = threadName, args = (self.badThingsQueue,self.stateQueue, self.pipe))
        thread.daemon = True
        return thread

    def start(self):
        packagerThread = threadMaker(self.packagerFunc, self.packagerName)
        socketThread = threadMaker(self.socketFunc, self.socketName)
        packagerThread.start()
        socketThread.start()

class udpSendClass(AnsibleHandler):
    SEND_PORT = 1235
    def __init__(self, badThingsQueue, stateQueue, pipe):
        packName = THREAD_NAMES.UDP_PACKAGER
        sockSendName = THREAD_NAMES.UDP_SENDER
        sendBuffer = TwoBuffer()
        super().__init__(self, packName, sockSendName, packageData, udpSender, badThingsQueue, stateQueue, pipe)

    ###Start Ansible Thread Chain###
    def packageData(badThingsQueue, stateQueue, pipe):#Run as a Process
        global sendBuffer
        while True:
            try:
                rawState = pipe.recv() #Pull state from the pipe
                if rawState == SM_COMMANDS.READY:
                    stateQueue.put([SM_COMMANDS.SEND, 1])
                elif rawState:
                    packState = package(rawState, badThingsQueue)
                    sendBuffer.replace(pack_state) ##Used list mutation as it's an atomic operation
            except Exception:
                badThingsQueue.put(BadThing(sys.exc_info(), None))

    def udpSender(badThingsQueue, stateQueue, pipe):
        host = socket.gethostname()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:#DGRAM for UDP sockets
            while True: #constantly send the state to Dawn
                try:
                    msg = sendBuffer.get()
                    if msg != 0: #check if the data inside the buffer has changed
                        s.sendto(msg, (host, udpSendClass.SEND_PORT))
                except Exception:
                    badThingsQueue.put(BadThing(sys.exc_info(), None))

    #Handles packaging and sending state to dawn in the form of protobuf we define
    def package(state, badThingsQueue):
        s = "TEST" #will be changed when we fully support protos
        b = bytearray()
        b.extend(map(ord, s))
        return b 

class udpRecvClass(AnsibleHandler):
    RECV_PORT = 1236
    def __init__(self, badThingsQueue, stateQueue, pipe):
        packName = THREAD_NAMES.UDP_UNPACKAGER
        sockRecvName = THREAD_NAMES.UDP_RECEIVER        
        recvBuffer = TwoBuffer()
        super().__init__(self, packName, sockRecvName, unpackageData, udpReceiver, badThingsQueue, stateQueue, pipe)

    def udpReceiver(badThingsQueue, stateQueue, pipe):
        #same thing as the client side from python docs
        host = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #DGRAM for UDP sockets
        s.bind((host, udpRecvClass.RECV_PORT))
        while True:
            try:
                data = s.recv(2048)
                recvBuffer.replace(data)
            except Exception: 
                badThingsQueue.put(BadThing(sys.exc_info(), None))

    def unpackageData(badThingsQueue, stateQueue, pipe):
        ready = False;
        while True:
            try:
                ready = pipe.recv()
                if ready:
                    unpackagedData = unpackage(recvBuffer.get())
                    stateQueue.put([SM_COMMANDS.STORE, unpackagedData])
            except Exception:
                badThingsQueue.put(BadThing(sys.exc_info(), None))

    ###Protobuf handlers###
    #Function for handling unpackaging of protobufs from Dawn
    def unpackage(data):
        return data #will be changed when we fully support protos
