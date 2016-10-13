import socket
import threading
import time
import fake_dawn
import random
import sys
from runtimeUtil import *

class TwoBuffer(): 
    """Custom buffer class for handling states.

    Holds two states, one which is updated and one that is sent. A list is used because
    it get and replace are atomic operations.

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
        thread = threading.Thread(target = threadTarget,
                                  name = threadName,
                                  args = (self.badThingsQueue, self.stateQueue, self.pipe))
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
        super().__init__(self, packName, sockSendName, udpSendClass.packageData,
                         udpSendClass.udpSender, badThingsQueue, stateQueue, pipe)

    def packageData(badThingsQueue, stateQueue, pipe):
        """Function run as a thread that packages data to be sent.

        The robot's current state is received from the StateManager via the pipe and packaged 
        by the package function, defined internally. The packaged data is then placed 
        back into the TwoBuffer replacing the previous state.
        """
        def package(state, badThingsQueue):
            """Helper function that packages the current state.

            Currently this function converts the input into bytes. This will
            eventually be implemented to package the rawState into protos.
            """
            s = "TEST" 
            b = bytearray()
            b.extend(map(ord, s))
            return b 

        global sendBuffer
        while True:
            try:
                rawState = pipe.recv() 
                if rawState == SM_COMMANDS.READY:
                    stateQueue.put([SM_COMMANDS.SEND, 1])
                elif rawState:
                    packState = package(rawState, badThingsQueue)
                    sendBuffer.replace(pack_state) 
            except Exception:
                badThingsQueue.put(BadThing(sys.exc_info(), None))

    def udpSender(badThingsQueue, stateQueue, pipe):
        """Function run as a thread that sends a packaged state from the TwoBuffer
        
        The current state that has already been pacakaged is gotten from the 
        TwoBuffer, and is sent to Dawn via a UDP socket.
        """
        host = socket.gethostname()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            while True: 
                try:
                    msg = sendBuffer.get()
                    if msg != 0: 
                        s.sendto(msg, (host, udpSendClass.SEND_PORT))
                except Exception:
                    badThingsQueue.put(BadThing(sys.exc_info(), None))


class udpRecvClass(AnsibleHandler):
    RECV_PORT = 1236
    def __init__(self, badThingsQueue, stateQueue, pipe):
        packName = THREAD_NAMES.UDP_UNPACKAGER
        sockRecvName = THREAD_NAMES.UDP_RECEIVER        
        recvBuffer = TwoBuffer()
        super().__init__(self, packName, sockRecvName, udpRecvClass.unpackageData,
                         udpRecvClass.udpReceiver, badThingsQueue, stateQueue, pipe)

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
        ###Protobuf handlers###
        #Function for handling unpackaging of protobufs from Dawn
        def unpackage(data):
            return data #will be changed when we fully support protos

        ready = False;
        while True:
            try:
                ready = pipe.recv()
                if ready:
                    unpackagedData = unpackage(recvBuffer.get())
                    stateQueue.put([SM_COMMANDS.STORE, unpackagedData])
            except Exception:
                badThingsQueue.put(BadThing(sys.exc_info(), None))

