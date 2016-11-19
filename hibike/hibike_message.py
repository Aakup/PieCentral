from __future__ import print_function
# Rewritten because Python.__version__ != 3
import struct
import pdb
import os
import json

config_file = open(os.path.join(os.path.dirname(__file__), 'hibikeDevices.json'), 'r')
devices = json.load(config_file)

paramMap = {device["id"]: {param["name"]: (param["number"], param["type"]) for param in device["params"]} for device in devices}
devices = {device["id"]: device for device in devices}
"""
structure of devices
{0: 
    {"id": 0, "name": "LimitSwitch", "params": [
                                               {"number": 0, "name": "switch0", "type": "bool", "read": True, "write": False}
                                               ]
    }
}

"""

# Dictionary mapping param types to python struct format characters
paramTypes = {
  "bool" : "?",
  "uint8_t": "B",
  "int8_t": "b", 
  "uint16_t": "H",
  "int16_t": "h", 
  "uint32_t": "I",
  "int32_t": "i", 
  "uint64_t": "Q",
  "int64_t": "q", 
  "float": "f",
  "double": "d"
}

# Dictionary of message types: message id
messageTypes = {
  "Ping" :                 0x10,
  "SubscriptionRequest" :  0x11,
  "SubscriptionResponse" : 0x12,
  "DeviceRead" :           0x13,
  "DeviceWrite" :          0x14,
  "DeviceData" :           0x15,
  "Error" :                0xFF
}

# Dictionary of device types: enumeration
deviceTypes = {
  "LimitSwitch"   :       0x00,
  "LineFollower"  :       0x01,
  "Potentiometer" :       0x02,
  "Encoder"       :       0x03,
  "BatteryBuzzer" :       0x04,
  "TeamFlag"      :       0x05,
  "Grizzly"       :       0x06,
  "ServoControl"  :       0x07,
  "LinearActuator":       0x08,
  "ColorSensor"   :       0x09,
  "DistanceSensor":       0x10,
  "MetalDetector" :       0x11,
  "ExampleDevice" :       0xFFFF
}

# Dictionary of error names : error codes
errorCodes = {
  "UnexpectedDelimiter" : 0xFD,
  "CheckumError"        : 0xFE,
  "GenericError"        : 0xFF
}

class HibikeMessage:
  def __init__(self, messageID, payload):
    assert messageID in messageTypes.values()
    self._messageID = messageID
    self._payload = payload[:]
    self._length = len(payload)

  def getmessageID(self):
    return self._messageID

  # Returns a copy of payload as a bytearray
  def getPayload(self):
    return self._payload[:]

  def toByte(self):
    m_buff = bytearray()
    m_buff.append(self._messageID)
    m_buff.append(self._length)
    m_buff.extend(self.getPayload())
    return m_buff

  def __str__(self):
    return str([self._messageID] + [self._length] + list(self._payload))

  def __repr__(self):
    return str(self)




# return the top 16 bits of UID
def getDeviceType(uid):
  return int(uid >> 72)

# return bits [71: 64] of the UID
def getYear(uid):
  temp = uid >> 64
  return int(temp & 0xFF)

# return bits[63: 0] of the UID
def getID(uid):
  return uid & 0xFFFFFFFFFFFFFFFF


# Given a message, computes the checksum
def checksum(data):
  # Remove this later after development
  assert type(data) == bytearray, "data must be a bytearray"

  chk = data[0]
  for i in range(1, len(data)):
    chk ^= data[i]
  return chk


  assert type(data) == bytearray, "data must be a bytearray"

  if len(data) % 2 != 0:
    data = data + bytearray([0])
  pairs = []

  for i in range(0, len(data), 2):
    first = data[i]
    first = first << 8
    first |= data[i+1]
    pairs.append(first)

  chk = pairs[0]
  for j in range(1, len(pairs)):
    chk += pairs[j]
    if chk >> 16 == 1:
      chk += 1
      chk &= 0xffff

  chk = ~chk
  chk &= 0xffff 
  if chk == 0:
    return 0xffff
  return chk



# Sends this message
# Computes the checksum
# Then sends each byte of the message, and finally sends the checksum byte
def send(serial_conn, message):
  m_buff = message.toByte()
  chk = checksum(m_buff)
  m_buff.append(chk)
  encoded = cobs_encode(m_buff)
  out_buf = bytearray([0x00, len(encoded)]) + encoded
  serial_conn.write(out_buf)



def make_ping():
  """ Makes and returns Ping message."""
  payload = bytearray()
  message = HibikeMessage(messageTypes["Ping"], payload)
  return message

def make_subscription_request(device_id, params, delay):
  """ Makes and returns SubscriptionRequest message.

      looks up config data about the specified 
      device_id to properly construct the message.
      
      device_id - a device type id (not uid).
      params    - an iterable of param names
      delay     - the delay in milliseconds
      struct.pack('%sf' % len(floatlist), *floatlist)
  """
  paramNums = [paramMap[device_id][name][0] for name in params]
  entries = [1 << num for num in paramNums]
  tot = 0
  for i in range(len(entries)):
    tot = tot ^ entries[i]
  temp_payload = struct.pack('<HH', tot, delay)
  payload = bytearray(temp_payload)
  message = HibikeMessage(messageTypes["SubscriptionRequest"], payload)
  return message
  

def make_subscription_response(device_id, params, delay, uid):
  """ Makes and returns SubscriptionResponse message.

      looks up config data about the specified 
      device_id to properly construct the message.
      
      device_id - a device type id (not uid).
      params    - an iterable of param names
      delay     - the delay in milliseconds
      uid       - the uid
  """
  raise NotImplementedError()

def make_device_read(device_id, params):
  """ Makes and returns DeviceRead message.

      looks up config data about the specified 
      device_id to properly construct the message.
      
      device_id - a device type id (not uid).
      params    - an iterable of param names
  """
  paramNums = [paramMap[device_id][name][0] for name in params]
  entries = [1 << num for num in paramNums]
  tot = 0
  for i in range(len(entries)):
    tot = tot ^ entries[i]
  temp_payload = struct.pack('<H', tot)
  payload = bytearray(temp_payload)
  message = HibikeMessage(messageTypes["DeviceRead"], payload)
  return message

def decode_params(device_id, params):
#     Decodes an inputted set of parameters that is in binary form   
#     Returns a list of names symbolizing the parameters encoded 
#
#     device_id - a device type id (not uid)
#     params    - the set of parameters in binary form
  converted_params = []
  for param_count in range(16):
     if (1 & (params >> param_count) == 1):
        converted_params.append(param_count)
  named_params = []
  for param in converted_params:
     if param >= len(devices[device_id]["params"]):
        break
     named_params.append(devices[device_id]["params"][param]["name"])
  return named_params
  
def make_device_write(device_id, params_and_values):
  """ Makes and returns DeviceWrite message.
      If all the params cannot fit, it will fill as many as it can.

      looks up config data about the specified 
      device_id to properly construct the message.
      
      device_id         - a device type id (not uid).
      params_and_values - an iterable of param (name, value) tuples
  """
  params_and_values = sorted(params_and_values, key=lambda x: paramMap[device_id][x[0]][0])
  params = [param[0] for param in params_and_values]
  paramNums = [paramMap[device_id][name][0] for name in params]
  paramT = [paramMap[device_id][name][1] for name in params]
  values = [param[1] for param in params_and_values]
  entries = [1 << num for num in paramNums]

  tot = 0
  for i in range(len(entries)):
    tot = tot ^ entries[i]
  typeString = '<H'
  for t in paramT:
    typeString += paramTypes[t]
  temp_payload = struct.pack(typeString, tot, *values)
  payload = bytearray(temp_payload)
  message = HibikeMessage(messageTypes["DeviceWrite"], payload)
  return message

def decode_device_write(device_id, message):
  messageID = message.getmessageID()
  payload = message.getPayload()
  messageT = "DeviceWrite"
  paramB = bin(payload[0])
  paramNames = decode_params(device_id, paramB)
  paramT = [paramMap[device_id][name][1] for name in paramNames]
  typeString = '<H'
  for t in paramT:
    typeString += paramTypes[t]
  tot_values = struct.unpack(typeString, payload)
  params_and_values = []
  for i in range(len(paramNames)):
    param_and_values.append((paramNames[i], tot_values[i+1]))
  return params_and_values









def make_device_data(device_id, params_and_values):
  """ Makes and returns SubscriptionRequest message.
      If all the params cannot fit, it will fill as many as it can.

      looks up config data about the specified 
      device_id to properly construct the message.
      
      device_id         - a device type id (not uid).
      params_and_values - an iterable of param (name, value) tuples
  """
  raise NotImplementedError()

def make_error(error_code):
  """ Makes and returns Error message."""
  temp_payload = struct.pack('<B', error_code)
  payload = bytearray(temp_payload)
  message = HibikeMessage(messageTypes["Error"], payload)
  return message

def parse_subscription_response(msg):
  assert msg.getmessageID() == messageTypes["SubscriptionResponse"]
  payload = msg.getPayload()
  assert len(payload) == 15
  params, delay, device_id, year, ID = struct.unpack("<HHHBQ", payload)
  params = decode_params(device_id, params)
  uid = (device_id << 72) | (year << 64) | ID
  return (params, delay, uid)

def parse_device_data(msg, device_id):
  assert msg.getmessageID() == messageTypes["DeviceData"]
  payload = msg.getPayload()
  assert len(payload) >= 2
  params,  =  struct.unpack("<H", payload[:2])
  params = decode_params(device_id, params)
  struct_format = "<"
  for param in params:
    struct_format += paramTypes[paramMap[device_id][param][1]]
  values = struct.unpack(struct_format, payload[2:])
  return list(zip(params, values))



def parse_bytes(bytes):
  if len(bytes) < 2:
    return None
  cobs_frame, message_size = struct.unpack('<BB', bytes[:2])
  if cobs_frame != 0 or len(bytes) < message_size + 2:
    return None
  message = cobs_decode(bytes[2:message_size+2])

  if len(message) < 2:
    return None
  messageID, payloadLength = struct.unpack('<BB', message[:2])
  if len(message) < 2 + payloadLength + 1:
    return None
  payload = message[2:2 + payloadLength]
  chk = struct.unpack('<B', message[2+payloadLength:2+payloadLength+1])[0]
  if chk != checksum(message[:-1]):
    #print(chk, checksum(message[:-1]), list(message))
    return None
  return HibikeMessage(messageID, payload)



def blocking_read(serial_conn):
  buffer = bytearray()
  while not parse_bytes(buffer):
    curr = serial_conn.read()
    if struct.unpack('<B', curr)[0] == 0:
      buffer = bytearray(curr)
    else:
      buffer.extend(curr)
  return parse_bytes(buffer)


# constructs a new object Message by continually reading from input
# Uses dictionary to figure out length of data to know how many bytes to read
# Returns:
    # None if no message
    # -1 if checksum does not match
    # Otherwise returns a new HibikeMessage with message contents
def read(serial_conn):
  
  # deal with cobs encoding
  while serial_conn.inWaiting() > 0:
    if struct.unpack('<B', serial_conn.read())[0] == 0:
      break
  else:
    return None
  message_size = struct.unpack('<B', serial_conn.read())[0]
  encoded_message = serial_conn.read(message_size)
  message = cobs_decode(encoded_message)
  

  if len(message) < 2:
    return None
  messageID, payloadLength = struct.unpack('<BB', message[:2])
  if len(message) < 2 + payloadLength + 1:
    return None
  payload = message[2:2 + payloadLength]

  chk = struct.unpack('<B', message[2+payloadLength:2+payloadLength+1])[0]
  if chk != checksum(message[:-1]):
    print(chk, checksum(message[:-1]), list(message))
    return -1

  return HibikeMessage(messageID, payload)

# cobs helper functions
def cobs_encode(data):
  output = bytearray()
  curr_block = bytearray()
  for byte in data:
    if byte:
      curr_block.append(byte)
      if len(curr_block) == 254:
        output.append(1 + len(curr_block))
        output.extend(curr_block)
        curr_block = bytearray()
    else:
      output.append(1 + len(curr_block))
      output.extend(curr_block)
      curr_block = bytearray()
  output.append(1 + len(curr_block))
  output.extend(curr_block)
  return output

def cobs_decode(data):
  output = bytearray()
  index = 0
  while (index < len(data)):
    block_size = data[index] - 1
    index += 1
    if index + block_size > len(data):
      return bytearray()
    output.extend(data[index:index + block_size])
    index += block_size
    if block_size + 1 < 255 and index < len(data):
      output.append(0)
  return output


class HibikeMessageException(Exception):
  pass
# Config file helper functions

def device_name_to_id(name):
  for device in devices.values():
    if device["name"] == name:
      return device["id"]
  raise HibikeMessageException("Invalid device name: %s" % name)

def device_id_to_name(id):
  for device in devices.values():
    if device["id"] == id:
      return device["name"]
  raise HibikeMessageException("Invalid device id: %d" % id)

def uid_to_device_name(uid):
  return device_id_to_name(uid_to_device_id(uid))

def uid_to_device_id(uid):
  return uid >> 72


def all_params_for_device_id(id):
  return list(paramMap[id].keys())
