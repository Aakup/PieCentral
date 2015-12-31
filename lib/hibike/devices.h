#ifndef DEVICES_H
#define DEVICES_H

typedef enum {
  LIMIT_SWITCH = 0x00,
  POTENTIOMETER = 0x02,
  TEAM_FLAG = 0x05,
  SERVO_CONTROL = 0x07,
  COLOR_SENSOR = 0x09,
  EXAMPLE_DEVICE = 0xFFFF
} deviceID;


#endif /* DEVICES_H */
