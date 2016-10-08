# Thing to do for Hibike

## Protocol Updates (hibike/protocol2.0)

Design, document and implementat the next version of the hibike protocol. See README.md in the hibike/protocol2.0 branch.

### Tasks:

- Test actual usb-serial throughput
	- currently unassigned
	- someone should test the actual bytes/second we can get between an adruino micro and a BBB
- Update protocol documentation
	- done
- Add message constructors hibike_message.py
	- assigned to Hong Jun
- Add message constructors lib/hibike
	- assigned to Tiffany
- Implement new packet structure on both sides
	- assigned to Caroline

## Python Rewrite / Concurrency (hibike/concurrency)

Rewrite hibike.py to implement concurrency more cleanly and efficiently.


### Tasks:

- Test having a read and write thread share a serial port
- Create runnable skeleton code

## Runtime-Hibike Integration / Simulation (hibike/atalanta)

Design a protocol for runtime-hibike communication over python multiprocessing Queues

Implement a runtime simulator that uses this protocol for testing.

### Tasks:

- Design and Document a provisional protocol; talk to runtime team
- Write a simulator for this protocol
	- Should expose a testing api similar to last year's hibike.py


## Virtual Smart Sensors (hibike/virtual)

Implement smart device simulators for testing hibike/runtime without physical sensors.

### Tasks:

- Write python clients that simulates the behavior of real smart devices
    - assigned to Ivan
- Write scripts to spawn/despawn these virtual devices and allow hibike to find them
    - Probably need some config file
- Make the virtual smart sensors to fail/behave erratically in different ways to test hibike
