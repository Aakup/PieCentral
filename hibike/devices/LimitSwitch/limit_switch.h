#ifndef EX_DEVICE_H
#define EX_DEVICE_H

#include "hibike_device.h"

//////////////// DEVICE UID ///////////////////
hibike_uid_t UID = {
  LIMIT_SWITCH,                      // Device Type
  0,                                 // Year
  UID_RANDOM,                        // ID
};
///////////////////////////////////////////////

#define NUM_SWITCHES 4
#define IN_0 A0
#define IN_1 A1
#define IN_2 A2
#define IN_3 A3

// function prototypes
void setup();
void loop();

uint8_t device_data_update(int param, uint8_t* data_update_buf, size_t buf_len)
uint32_t device_write(uint8_t param, uint8_t* data, size_t len)

#endif /* EX_DEVICE_H */