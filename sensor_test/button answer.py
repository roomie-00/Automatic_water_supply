
import RPi.GPIO as GPIO
import I2C_LCD_driver
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN, pull_up_down = GPIO.PUD_UP)

mylcd = I2C_LCD_driver.lcd()

try:
    flag = False
    while True:
        button_state = GPIO.input(16)
        if button_state == False:
            if flag:
                flag = False
            else:
                flag = True
        if flag:
            mylcd.lcd_display_string("1", 1)
            time.sleep(0.2)

except KeyboardInterrupt:
    GPIO.cleanup()