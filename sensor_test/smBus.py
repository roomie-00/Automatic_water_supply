import smbus
import time
i2c = smbus.SMBus(1)
i2c.write_byte(0x27, 0x08)
time.sleep(3)
i2c.write_byte(0x27, 0x00)
i2c.read_byte(0x27)