# hibike 2.0!
Hibike is a lightweight communications protocol designed for the passing of sensor data for the 
PiE Robotics Kit, a.k.a Frank or "Kit Minimum" to some.

#### This branch contains documentation and implementation for the 2016-2017 version of the hibike protocol, which should feature iterative improvements over last year's protocol

#### These suggestions should make their way into protocol documentation first, then implemented in code. The basic read/write functions need to be implemented in Python, and everything needs to be implemented in Arduino, before merging this branch back to develop.

## Suggested Protocol Changes (Please make suggestions)

1. The checksum should be changed to something more robust
    - Janet suggested using UDP's checksum
2. COBS encoding should be implemented cleaner
    - It should be documented and part of the protocol itself, not a wrapper around it
    - There should not be a redundant length field
    - Only the first 2 bytes of a packet should not be cobs encoded
        - 0 byte and packet length
3. Data Update and Device Update/Status should be unified
    - Huge advantage: The BBB polling, writing, and subscribing can have identical responses from SD, and runtime can treat them the same
    - Protocol can abstract a device as only key value pairs
        - Current implementaion has key value pairs and one custom "data update" struct per device
        - Custom "data update struct" is nice because it is the exact size we need
        - Only Key Value pairs means 32 bits per digital IO pin...
        - Does ease of abstraction and implementaion justify larger packet length?
        - Is packet length significant anyways?
            - 32 bits at 115200 baud is .2 milliseconds?
            - Someone should test actual throughput
                - Especially how fast BBB can actually receive data
                - Even when doing blocking reads byte by byte in python?
                - While runtime and student code are running?
                - With 20+ devices?
        - Should the size of values be unique to reduce packet length?
            - Harder to implement
            - Both devices need to know the size of each value
                - But they needed to know the types anyways so maybe this is ok
    - SubRequest can specify which keys it wants to receive
        - Each DataUpdate will have to also encode this information to be stateless
        - What if we subscribe to more than the max payload size?
            - Just respond with as many as you can fit?
            - Error Packet?
        - A uint16_t bitmask could work? 16 keys is plenty for a device
4. Unused packets should be removed from the protocol
    - DescriptionRequest and Response are redundant
        - maintaing one config file is better for production
    - Do we have a use for the error packet yet?
        - Maybe when SD receives write requests for a read only key?
        - Maybe when a checksum fails/unexpected 0 byte is seen?
            - Can there be infinite loops of back and forth error packets?
            - Maybe only SD can send errors, and they'll only be used for logging statistics
5. Hot-Plugging behaviour should be optimized and well-defined
    - Current status quo (rebooting BBB to add devices) is unacceptable
    - Reenmerate devices every x seconds and also when runtime requests it
        - Or runtime can just request it every x seconds
    - Hibike can notify runtime when a device disconnects/connects
    - Student code accessing disconnected devices should raise a well-defined exception in *student code*
    - If a SD disconnects, will BBB find out until it tries reenumerating it?
        - If so, should BBB even bother reenumerating SDs it hasn't detected as disconnected?



## Section 0: A Quick Introduction

We make a few starting assumptions concerning the endpoints of communication: the device controlling a sensor is a Smart Device (SD), and a Beaglebone Black (BBB) is used as the central control board of each robot and thus is in charge of communicating with each Smart Device. These two communicate with each other via serial: the Beaglebone running pySerial and the Smart Device by using the built-in serial library. As each Smart Device communicates with the Beaglebone on its own separate port, we conveniently have no need to worry about any race conditions or other problems arising from concurrency.

Hibike abstracts every Smart Device as a set of (parameter,value) pairs.

The hibike protocol supports three ways of interacting with these parameters:
- Subscribing to regular updates of specific paramters
- Polling specific parameters
- Writing to specific parameters

Refer to Section 6 for an outline of the general behavior of the Hibike protocol.


## Section 1: General Message Structure
All messages have the relatively simple structure of Message ID, Payload, and Checksum as
depicted below. A more complete description of each field is given below the diagram.

    +------------+------------------+---------------------+------------+
    | Message ID |  Payload Length  |       Payload       |  Checksum  |
    |  (8 bits)  |      (8 bits)    |   (length varies)   |  (8 bits)  |
    +------------+------------------+---------------------+------------+

- Message ID 
  - an 8-bit ID specifying the type of message being sent or received. 
  - More information about each message type is specified in the following sections.

- Payload Length 
  - an 8-bit unsigned integer specifying the number of bytes in the payload

- Payload
  - Varies wildly depending on the type of message being sent. 
  - This will, of course, be described in more detail in Section 4.

- Checksum
  - An 8-bit checksum placed at the very end of every message. 
  - Really, any checksum scheme appending 8-bits to the end of the message will do, but an exceedingly simple one recommended exactly for its simplicity is making the checksum the XOR of every other byte in the message.

## Section 2: UID Format
Each Smart Device will be assigned an 88-bit UID with the following data.

    +-------------------+--------------+-----------------------------+
    |     Device Type   |     Year     |             ID              |
    |      (16 bits)    |   (8 bits)   |          (64 bits)          |
    +-------------------+--------------+-----------------------------+

- Device Type
    - 16-bit ID specifying the Type of a Smart Device
    - Device types are enumerated in Section 5

- Year
  - 8-bit ID corresponding to the competition year that the Smart Device was manufactured for. 
  - The 2015-2016 season will correspond to 0x00

- ID
    - Randomly generated 64-bit number that will uniquely identify each Smart Device within a specific device type and year.
    - With 64-bit IDs, the probability of a hash collision with 1000 of 1 type of device per year is roughly 0.05%


## Section 3: Parameters and bitmaps
- Hibike abstracts every smart device as a set of parameters that map to values
- Each smart device contains some number of paramaters, which can be read/written to.

- Paramaters can have many types, such as bool, int, short, byte, float, etc.
- Some paramaters are read only, some are write only, and some support both.
- A config file will describe the paramaters for each Device Type (name, type, permissions).
- Some packets encode sets of parameters in the form of bitmaps.




    ```
    +-------------------+-----------------------------+     +-----------------------------+
    |      Params       |         Value 0             | ... |         Value 15            |
    |     (16 bits)     |  (Optional and Variable)    |     |  (Optional and Variable)    |
    +-------------------+-----------------------------+     +-----------------------------+
    ```

- Params - 16-bit bitmap describing a set of parameters. The nth bit of Params, where the LSB is the 0th bit, references the nth paramater of a device.

- Value[0-15] - DeviceWrite and DeviceData send actual values for each param in Params. The value field for param n will only be present if bit n in Params is set. The size and type of each value field depends on param number and device type, and is described in a config file.


## Section 4: Enumerations

Message ID Enumeration:

|   ID    |       Message Type       |
|---------|--------------------------|
|  0x10   |          Ping            |
|  0x11   |   Subscription Request   |
|  0x12   |   Subscription Response  |
|  0x13   |       Device Read        |
|  0x14   |       Device Write       |
|  0x15   |      Device Data         |
|  0xFF   |           Error          |

Device Type Enumeration:

|   ID    |    Sensor      | Param Number | Param Name | Param Type | Read? | Write? |
|---------|----------------|--------------|------------|------------|-------|--------|
|  0x00   | LimitSwitch    | 0            | switch0    | bool       | yes   | no     |
|         |                | 1            | switch1    | bool       | yes   | no     |
|         |                | 2            | switch2    | bool       | yes   | no     |
|         |                | 3            | switch3    | bool       | yes   | no     |
|  0x01   | LineFollower   | 0            | left       | float      | yes   | no     |
|         |                | 1            | center     | float      | yes   | no     |
|         |                | 2            | right      | float      | yes   | no     |
|  0x02   | Potentiometer  | 0            | pot0       | float      | yes   | no     |
|         |                | 1            | pot1       | float      | yes   | no     |
|         |                | 2            | pot2       | float      | yes   | no     |
|         |                | 3            | pot3       | float      | yes   | no     |
|  0x03   | Encoder        | 0            | rotation   | int16_t    | yes   | no     |
|  0x04   | BatteryBuzzer  | 0            | connected  | bool       | yes   | no     |
|         |                | 1            | safe       | bool       | yes   | no     |
|         |                | 2            | cell1      | float      | yes   | no     |
|         |                | 3            | cell2      | float      | yes   | no     |
|         |                | 4            | cell3      | float      | yes   | no     |
|         |                | 5            | total      | float      | yes   | no     |
|         |                | 6            | calibrate | bool       | no    | yes    |
|  0x05   | TeamFlag       | 0            | mode       | bool       | yes   | yes    |
|         |                | 1            | blue       | bool       | yes   | yes    |
|         |                | 2            | yellow     | bool       | yes   | yes    |
|         |                | 3            | s1         | bool       | yes   | yes    |
|         |                | 4            | s2         | bool       | yes   | yes    |
|         |                | 5            | s3         | bool       | yes   | yes    |
|         |                | 6            | s3         | bool       | yes   | yes    |
|  0x06   | Grizzly        |              |            |            |       |        |
|  0x07   | ServoControl   | 0            | servo0     | uint8_t    | yes   | yes    |
|         |                | 1            | enable0    | bool       | yes   | yes    |
|         |                | 2            | servo1     | uint8_t    | yes   | yes    |
|         |                | 3            | enable1    | bool       | yes   | yes    |
|         |                | 4            | servo2     | uint8_t    | yes   | yes    |
|         |                | 5            | enable2    | bool       | yes   | yes    |
|         |                | 6            | servo3     | uint8_t    | yes   | yes    |
|         |                | 7            | enable3    | bool       | yes   | yes    |
|  0x08   | LinearActuator |              |            |            |       |        |
|  0x09   | ColorSensor    |              |            |            |       |        |
|  0x10   | DistanceSensor |              |            |            |       |        |
|  0x11   | MetalDetector  |              |            |            |       |        |
|  0xFFFF | ExampleDevice  | 0            | kumiko     | bool       | yes   | yes    |
|         |                | 1            | hazuki     | uint8_t    | yes   | yes    |
|         |                | 2            | sapphire   | int8_t     | yes   | yes    |
|         |                | 3            | reina      | uint16_t   | yes   | yes    |
|         |                | 4            | asuka      | int16_t    | yes   | yes    |
|         |                | 5            | haruka     | uint32_t   | yes   | yes    |
|         |                | 6            | kaori      | int32_t    | yes   | yes    |
|         |                | 7            | natsuki    | uint64_t   | yes   | yes    |
|         |                | 8            | yuko       | int64_t    | yes   | yes    |
|         |                | 9            | mizore     | float      | yes   | yes    |
|         |                | 10           | nozomi     | double     | yes   | yes    |
|         |                | 11           | shuichi    | uint8_t    | yes   | no     |
|         |                | 12           | takuya     | uint16_t   | no    | yes    |
|         |                | 13           | riko       | uint32_t   | yes   | no     |
|         |                | 14           | aoi        | uint64_t   | no    | yes    |
|         |                | 15           | noboru     | float      | yes   | no     |


     
Note: These assignments are totally random as of now. We need to figure
      out exactly what devices we are supporting.
Note: As of now, Grizzlies are not supported by Hibike (pyGrizzly should 
      be used instead) But they should be in the near future, to preserve 
      the idea of treating every peripheral as a SmartDevice.

Error ID Enumeration:

| Status  |    Meaning                    |
|---------|-------------------------------|
|   0xFD  |  Unexpected Packet Delimiter  |
|   0xFE  | Checksum Error                |
|   0xFF  | Generic Error                 |

Note: These assignments are also fairly random and may not all even be
      needed.

## Section 5: Message Descriptions



1. Ping: BBB pings SD for enumeration purposes.
         The SD will respond with a Sub Response packet.
     
    Payload format:

        +---------------+
        |     Empty     |
        |    (0 bits)   |
        +---------------+

    Direction:
    BBB --> SD

2. Sub Request: BBB requests data to be returned at a given interval. 
    - Params is a bitmap of paramaters being subscribed to. 
    - The SD will respond with a Sub Response packet 
      with a delay and bitmap of params it will acutally send values for,
      which may not be what was requested, due to nonexistent and write-only parameters.
    - If too many parameters are subscribed to, the Smart Device may have to send multiple DeviceData packets at each interval.
    - A delay of 0 indicates that the BBB does not want to receive data.
    - Non-zero delay with 0 Params will still subscribe to empty updates!!!

    Payload format:

        +---------------+---------------+
        |     Params    |     Delay     |
        |   (16 bits)   |   (16 bits)   |
        +---------------+---------------+

    Direction:
    BBB --> SD

3. Sub Response: SD sends (essentially) an ACK packet with its UID, Params subscribed to, and delay
    
  Payload format:

        +---------------+--------------------+--------------------------+
        |     Params    |       Delay        |          UID             |
        |   (16 bits)   |     (16 bits)      |       (88 bits)          |
        +---------------+--------------------+--------------------------+

    Direction:
    BBB <-- SD

4. Device Read: BBB requests some values from the SD. 
    - The SD should respond with DeviceData packets with values for all the readable params that were requested. 
    - If all the values cannot fit in one packet, multiple will be sent.
    
  Payload format:

        +---------------+
        |     Params    |
        |    (16 bits)  |
        +---------------+

    Direction:
    BBB --> SD

5. Device Write: BBB writes attempts to write values to some parameters.
    - The SD should respond with a DeviceData packet describing the readable params that were actually written to. 
    - The protocol currently does not support any ACK for write only params.
    
  Payload format:

        +-------------------+-----------------------------+     +-----------------------------+
        |      Params       |         Value 0             | ... |         Value 15            |
        |     (16 bits)     |  (Optional and Variable)    |     |  (Optional and Variable)    |
        +-------------------+-----------------------------+     +-----------------------------+

    Direction:
    BBB --> SD

6. Device Data: SD sends the values of some of its paramters. 
    - This can occur in response to a DeviceWrite/DeviceRead, or when the interval for a SubscriptionResponse occurs.
    
  Payload format:


        +-------------------+-----------------------------+     +-----------------------------+
        |      Params       |         Value 0             | ... |         Value 15            |
        |     (16 bits)     |  (Optional and Variable)    |     |  (Optional and Variable)    |
        +-------------------+-----------------------------+     +-----------------------------+

    Direction:
    BBB <-- SD

7. Error Packet: Sent to indicate an error occured. 
    - Currently only used for the BBB to log statistics.
    
  Payload format:

        +----------------+
        |   Error Code   |
        |    (8 bits)    |
        +----------------+

    Direction:
    BBB <-- SD

## Section 6: General Behavior
Setup

  1. The BBB sends a Ping packet to every serial port both when booting up,
     at regular hardcoded intervals, and whenever runtime asks. The responses
     to pings are used to enumerate Smart Devices, and allows hibike to support
     hot-plugging. Hot-unplugging will likely be supported too.
  2. The BBB will then subscribe to some paramters of some devices based on its needs.
      - Subscriptions can be changed at any time with SubscriptionRequest packets.
  3. Each supported device will have an entry in a config file that
     describe its paramters.

Sensor Communication (Reading values)

  1. After setup the BBB sends the approrpiate SubscriptionRequest 
     Packet is sent to each device.
  2. The SD will then return values at regular intervals specified by
     the Subscription Request (delay field)
  3. Hibike also allows for the BBB to poll parameters using a DeviceRead Packet.
  4. The SD will respond by returning a DeviceData Packet with 
     the values of the params specified.
   - Multiple DeviceData Packets may be sent due to packet size

Actuator Communication (Writing values)

  1. The BBB can write data to a some parameters of the
     SD with a Device Write Packet
  2. The SD will then return a DeviceData Packet with the new
     Values of each readable param that was written to. Write only
     params will not be a part of the DeviceData packet, but an empty
     DeviceData packet may still be sent.

Error handling

  1. Still kind of up in the air, but in general, only the BBB will
     have error handling behavior
  3. If a SD recieves an invalid packet, it will send an error packet.
