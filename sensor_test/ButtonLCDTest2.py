import time

import RPi.GPIO as GPIO  # 라즈베리파이 GPIO 관련 모듈을 불러옴

import I2C_LCD_driver
mylcd = I2C_LCD_driver.lcd()
GPIO.setmode(GPIO.BCM)
LCD = 2 # LCD 핀은 라즈베리파이 GPIO 2번핀으로
button = 15
GPIO.setup(button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# 스위치 핀을 풀다운저항이 있는 출력으로 설정
# 풀다운 저항이 있으면 버튼을 누르지 않으면 LOW 신호가 됨
# 여기를 GPIO.PUD_UP으로 하면 버튼을 누르지 않으면 HIGH 신호가 됨

def button_pressed_callback(channel):
    print("Button pressed!")

try:
    volume = [" 50ml", "100ml", "150ml", "200ml"]
    buttonClickCount = 0 # 0, 1, 2, 3 인덱스 참조용
    while True:
        if GPIO.input(button) == GPIO.HIGH:
            # 안 눌렀을 때
            mylcd.lcd_display_string("set up to " + volume[buttonClickCount], 1)

        else:
            # 눌렀을 때
            buttonClickCount += 1
            if buttonClickCount >= 4:
                # 버튼이 4 이상이 되면 다시 원점으로 돌아와야 함
                buttonClickCount = 0
            time.sleep(0.5)


finally:
    GPIO.cleanup()