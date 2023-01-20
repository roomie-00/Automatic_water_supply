import time

import RPi.GPIO as GPIO  # 라즈베리파이 GPIO 관련 모듈을 불러옴

import I2C_LCD_driver
mylcd = I2C_LCD_driver.lcd()
GPIO.setmode(GPIO.BCM)
LCD = 2 # LCD 핀은 라즈베리파이 GPIO 2번핀으로

button_volume = 6 # 용량 버튼(초록색)
button_cycle = 15 # 주기 버튼(빨간색)

GPIO.setup(button_volume, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.setup(button_cycle, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# 스위치 핀을 풀다운저항이 있는 출력으로 설정
# 풀다운 저항이 있으면 버튼을 누르지 않으면 LOW 신호가 됨
# 여기를 GPIO.PUD_UP으로 하면 버튼을 누르지 않으면 HIGH 신호가 됨

try:
    volume = ["100 (ml)", "150 (ml)", "200 (ml)", "250 (ml)"]
    cycle = ["01 (min)", "10 (min)", "20 (min)", "30 (min)"]
    buttonClickCount_volume = 0 # 0, 1, 2, 3 인덱스 참조용
    buttonClickCount_cycle = 0 # 0, 1, 2 인덱스 참조용
    while True:
        if GPIO.input(button_volume) == GPIO.HIGH:
            # 안 눌렀을 때
            mylcd.lcd_display_string("volume: " + volume[buttonClickCount_volume], 1)
        else:
            # 눌렀을 때
            buttonClickCount_volume += 1
            if buttonClickCount_volume >= len(volume):
                # 버튼이 4 이상이 되면 다시 원점으로 돌아와야 함
                buttonClickCount_volume = 0
            time.sleep(0.5)

        if GPIO.input(button_cycle) == GPIO.HIGH:
            # 안 눌렀을 때
            mylcd.lcd_display_string(" cycle: " + cycle[buttonClickCount_cycle], 2)
        else:
            # 눌렀을 때
            buttonClickCount_cycle += 1
            if buttonClickCount_cycle >= len(cycle):
                # 버튼이 4 이상이 되면 다시 원점으로 돌아와야 함
                buttonClickCount_cycle = 0
            time.sleep(0.5)


finally:
    GPIO.cleanup()