import struct
import serial
import hibike_message as hm
import sys
import random
import time
"""
This program should create a virtual hibike device for testing purposes

usage:
$ socat -d -d pty,raw,echo=0 pty,raw,echo=0
2016/09/20 21:29:03 socat[4165] N PTY is /dev/pts/26
2016/09/20 21:29:03 socat[4165] N PTY is /dev/pts/27
2016/09/20 21:29:03 socat[4165] N starting data transfer loop with FDs [3,3] and [5,5]
$ python3.5 virtual_device.py -d LimitSwitch -p /dev/pts/26
"""

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--device', required=True, help='device type')
parser.add_argument('-p', '--port', required=True, help='serial port')
args = parser.parse_args()

device = args.device
port = args.port
print(device, port)
conn = serial.Serial(port, 115200)

device_id = hm.deviceTypes[device]
year = 1
id = random.randint(0, 0xFFFFFFFFFFFFFFFF)
delay = 0
updateTime = 0
uid = (device_id << 72) | (year << 64) | id

# Here, the parameters and values to be sent in device datas are set for each device type, the list of subscribed parameters is set to empty,
if device_type in [hm.deviceTypes["LimitSwitch"]]: 
        subscribed_params = 0
        params_and_values = [(hm.devices["switch0"], True), (hm.devices["switch1"], True), (hm.devices["switch2"], False), (hm.devices["switch3"], False)]
if device_type in [hm.deviceTypes["ServoControl"]]:
        subscribed_params = 0
        params_and_values = [(hm.devices["servo0"], 2), (hm.devices["enable0"], True), (hm.devices["servo1"], 0), (hm.devices["enable1"], True), (hm.devices["servo2"], 5), (hm.devices["enable2"], True), (hm.devices["servo3"], 3), (hm.devices["enable3"], False)]

while (True):
        if (updateTime != 0 and delay != 0):
                if((time.time() - updateTime) >= (delay * 0.001)): #If the time equal to the delay has elapsed since the previous device data, send a device data with the device id and the device's subscribed params and values
                        data = 0
                        for data_tuple in params_and_values:
                                if data_tuple[0] in subscribed_params:
                                        data.append[data_tuple]
                        hm.send(conn, hm.make_device_data(device_id, data))
                        updateTime = time.time()

             
        msg = hm.read(conn)
        if not msg:
             time.sleep(.0005)
             continue
        if msg.getmessageID() in [hm.messageTypes["SubscriptionRequest"]]: #Update the delay, subscription time, and params, then send a subscription response 
             params, delay = struct.unpack("<HH", msg.getPayload())
             
             subscribed_params = hm.decode_params(device_id, params)
             hm.send(conn, hm.make_subscription_response(device_id, subscribed_params, delay, uid))
             updateTime = time.time()
        if msg.getmessageID() in [hm.messageTypes["Ping"]]: # Send a subscription response 
             hm.send(conn, hm.make_subscription_response(device_id, subscribed_params, delay, uid))
        if msg.getmessageID() in [hm.messageTypes["DeviceRead"]]: 
# Send a device data with the requested param and value tuples
             params = struct.unpack("<H", msg.getPayload())
             read_params = hm.decode_params(device_id, params)
             read_data = 0
          
             for data_tuple in params_and_values:
                if data_tuple[0] in read_params:
                     if hm.devices[device_id]["params"][data_tuple[0]]["read"] != True:# Raise a syntax error if one of the values to be read is not readable
                             raise SyntaxError("Attempted to read an unreadable value")
                     read_data.append(data_tuple)
             hm.send(conn, hm.make_device_data(device_id, read_data))
           
        if msg.getmessageID() in [hm.messageTypes["DeviceWrite"]]:
# Write to requested parameters and return the values of the parameters written to using a device data
                params = struct.unpack("<H", msg.getPayload()[0:2])
                write_params = hm.decode_params(device_id, params)
                
                value_types = [hm.paramMap[device_id][name][1] for name in write_params]
                type_string = "<"
                for val_type in value_types:
                     type_string += hm.paramTypes[val_type]
                values = struct.unpack(type_string, msg.getPayload()[2:])
                write_tuples = [(write_params[index], values[index]) for index in range(len(write_params))]

                for data_tuple in params_and_values:
                     if data_tuple[0] in write_params:
                          if hm.devices[device_id]["params"][data_tuple[0]]["write"] != True: # Raise a syntax error if the value that the message attempted to write to is not writable
                                raise SyntaxError("Attempted to write to an unwritable value")
                          data_tuple = write_tuples[write_params.index(data_tuple[0])]

                # Send the written data, make sure you only send data for readable parameters
                for index in range(len(write_params)):
                        while (hm.devices[device_id]["params"][write_tuples[index][0]]["read"] != True):
                             del write_tuples[index]
                hm.send(conn, hm.make_device_data(device_id, write_tuples))
           
                