import RPi.GPIO as GPIO
import time
mylcd = I2C_LCD_driver.lcd()
GPIO.setmode(GPIO.BCM)
LCD = 2, 3 # ??
button = 18
GPIO.setup(LCD, GPIO.OUT)
GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# 스위치 핀을 풀다운저항이 있는 출력으로 설정
# 풀다운 저항이 있으면 버튼을 누르지 않으면 LOW 신호가 됨
# 여기를 GPIO.PUD_UP으로 하면 버튼을 누르지 않으면 HIGH 신호가 됨

try:
    while True:
        volume = ["50ml", "100ml", "150ml", "200ml"]
        if GPIO.input(button) == GPIO.HIGH:
            GPIO.output(LCD, True)
            for i in range(len(volume)):
                mylcd.lcd_display_string("set to {volume[i]}", 1)
        else:
            GPIO.output(LCD, False)
        time.sleep(0.3)
finally:
    GPIO.cleanup()