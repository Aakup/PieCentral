import socket
import threading
import time
import random
import sys

from runtimeUtil import *

class TwoBuffer(): 
    """Custom buffer class for handling states.

    Holds two states, one which is updated and one that is sent. A list is used because
    the get and replace methods are atomic operations. Replacing swaps indices of the 
    get and put index.

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
    """Parent class for UDP Processes that spawns threads 

    Initializes generalized instance variables for both UDP sender and receiver, and creates a callable
    method to initialize the two threads per UDP process and start them. 
    """
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
                                  args = (self, self.badThingsQueue, self.stateQueue, self.pipe))
        thread.daemon = True
        return thread

    def start(self):
        try:
            packagerThread = self.threadMaker(self.packagerFunc, self.packagerName)
        except:
            print("Packager thread failed to spawn")
        socketThread = self.threadMaker(self.socketFunc, self.socketName)
        try:
            packagerThread.start()
        except:
            print("Packager thread failed to start")
        socketThread.start()
        while True:
            time.sleep(1)



class UDPSendClass(AnsibleHandler):
    SEND_PORT = 1235

    def __init__(self, badThingsQueue, stateQueue, pipe):
        self.sendBuffer = TwoBuffer()
        packagerName = THREAD_NAMES.UDP_PACKAGER
        sockSendName = THREAD_NAMES.UDP_SENDER
        super().__init__(packagerName, sockSendName, UDPSendClass.packageData,
                         UDPSendClass.udpSender, badThingsQueue, stateQueue, pipe)

    def packageData(self, badThingsQueue, stateQueue, pipe):
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

        while True:
            try:
                stateQueue.put([SM_COMMANDS.SEND_ANSIBLE, []])
                rawState = pipe.recv()
                if rawState == RUNTIME_CONFIG.PIPE_READY:
                    stateQueue.put([SM_COMMANDS.SEND_ANSIBLE, []])
                elif rawState:
                    packState = package(rawState, badThingsQueue)
                    self.sendBuffer.replace(packState) 
            except Exception:
                badThingsQueue.put(BadThing(sys.exc_info(), 
                    "UDP packager thread has crashed with error:",  
                    event = BAD_EVENTS.UDP_SEND_ERROR, 
                    printStackTrace = True))

    def udpSender(self, badThingsQueue, stateQueue, pipe):
        """Function run as a thread that sends a packaged state from the TwoBuffer
        
        The current state that has already been packaged is gotten from the 
        TwoBuffer, and is sent to Dawn via a UDP socket.
        """
        host = socket.gethostname() #TODO: determine host in runtime-dawn comm
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            while True: 
                try:
                    msg = self.sendBuffer.get()
                    if msg != 0: 
                        s.sendto(msg, (host, UDPSendClass.SEND_PORT))
                except Exception:
                    badThingsQueue.put(BadThing(sys.exc_info(), 
                    "UDP sender thread has crashed with error:",  
                    event = BAD_EVENTS.UDP_SEND_ERROR, 
                    printStackTrace = True))

class UDPRecvClass(AnsibleHandler):
    RECV_PORT = 1236
    
    def __init__(self, badThingsQueue, stateQueue, pipe):
        self.recvBuffer = TwoBuffer()        
        packName = THREAD_NAMES.UDP_UNPACKAGER
        sockRecvName = THREAD_NAMES.UDP_RECEIVER
        super().__init__(packName, sockRecvName, UDPRecvClass.unpackageData,
                         UDPRecvClass.udpReceiver, badThingsQueue, stateQueue, pipe)

    def udpReceiver(self, badThingsQueue, stateQueue, pipe):
        """Function to receive data from Dawn to local TwoBuffer

        Listens on the receive port and stores data into TwoBuffer to be shared
        with the unpackager.
        """
        host = socket.gethostname() #TODO: determine host between dawn-runtime comm
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        s.bind((host, UDPRecvClass.RECV_PORT))
        while True:
            try:
                data = s.recv(2048)
                self.recvBuffer.replace(data)
            except Exception as e:
                    badThingsQueue.put(BadThing(sys.exc_info(), 
                    "UDP receiver thread has crashed with error:",  
                    event = BAD_EVENTS.UDP_RECV_ERROR, 
                    printStackTrace = True))

    def unpackageData(self, badThingsQueue, stateQueue, pipe):
        """Unpackages data from proto and sends to stateManager on the SM stateQueue

        Sending data from dawn to stateManager is supported, the unpackage function is
        currently unimplemented.  
        """
        def unpackage(data):
            """Function that takes a packaged proto and unpackages item

            Currently simply returns the original data. Needs to be implemented
            """
            return data 

        ready = False;
        while True:
            try:
                ready = pipe.recv()
                if ready:
                    unpackagedData = unpackage(self.recvBuffer.get())
                    stateQueue.put([SM_COMMANDS.RECV_ANSIBLE, unpackagedData])
            except Exception as e:
                    badThingsQueue.put(BadThing(sys.exc_info(), 
                    "UDP sender thread has crashed with error:",  
                    event = BAD_EVENTS.UDP_RECV_ERROR, 
                    printStackTrace = True))
                    