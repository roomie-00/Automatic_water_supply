import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN)
count = 50

while True:
    value = GPIO.input(16)
    if value == True:
        count += 50
        time.sleep(0.1)
        print(count)
    time.sleep(0.1)