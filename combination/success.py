import RPi.GPIO as GPIO
import time
import threading
import signal
import sys

import spidev
import I2C_LCD_driver                                              # 버튼 관련
from hx711 import HX711                                            # hx711
import pickle
import os

# -----------------------------------------------------------------------------------------
# GPIO setting
GPIO.setmode(GPIO.BCM)                                             # BCM 모드

# 스위치 핀을 풀다운저항이 있는 출력으로 설정
# 풀다운 저항이 있으면 버튼을 누르지 않으면 LOW 신호가 됨
# 여기를 GPIO.PUD_UP으로 하면 버튼을 누르지 않으면 HIGH 신호가 됨
volume_button = 15  # 용량 버튼 핀번호
GPIO.setup(volume_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
period_button = 6  # 주기 버튼 핀번호
GPIO.setup(period_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

LCD = 2                                                             # LCD 핀번호
hx = HX711(dout_pin=20, pd_sck_pin=16)                              # 핀번호 DT(20) -> 센서 데이터 신호 / SCK(16) -> 센서 제어용 신호

piezo = 26                                                          # piezo 핀번호
GPIO.setup(piezo, GPIO.OUT)                                         # 출력

PUMP = 12                                                           # 워터펌프 핀번호
GPIO.setup(PUMP, GPIO.OUT)                                          # 워터펌프 물 나오게
spi = spidev.SpiDev()                                               # Open Spi Bus
spi.open(0, 0)                                                      # SPI 버스 0과 디바이스 0을 연다. open(bus, device)
spi.max_speed_hz = 1000000                                          # 최대 전송 속도를 1MHz로 설정
# ------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------
# 그 외 setting
# 임계값
water_percent_threshold = 30

## 주기 조절 버튼 + 용량 조절 버튼 + LCD 표시 세팅 시작 ##
mylcd = I2C_LCD_driver.lcd()

volume = [50, 75, 100, 150, 200]
period = [1, 10, 20, 30]
volume_sec = [2, 3, 4, 6, 8]

start = 1
buttonClick_set = 0
buttonClickCount_volume = 0                                         # 0, 1, 2, 3 인덱스 참조용
buttonClickCount_period = 0                                         # 0, 1, 2 인덱스 참조용

result_volume = volume[buttonClickCount_volume]
result_period = period[buttonClickCount_period]

# thread 관련
water_do = False
button_lock = threading.Lock()                                      # Lock Instance 생성
water_pump_lock = threading.Lock()                                  # Lock Instance 생성
evt = threading.Event()                                             # Event 객체 생성 default flag=0
cv = threading.Condition()                                          # condition 관리
# ------------------------------------------------------------------------------------------

# 키보드 인터럽트 걸리면 빠져 나오는 용도
def signal_handler(signal, frame):
    print('process stop')
    GPIO.cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# To read SPI data from MCP3008 chip
# Channel must be 0~7 integer
def readChannel(channel):
    val = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((val[1] & 3) << 8) + val[2]
    return data


# 0~1023 value가 들어옴. 1023이 수분함량 min값
def convertPercent(data):
    return 100.0 - round(((data * 100) / float(1023)), 1)


def func_b():
    global water_do
    global mylcd
    global volume
    global period
    global buttonClickCount_period
    global buttonClickCount_volume

    try:
        mylcd.lcd_display_string("volume: " + str(volume[buttonClickCount_volume]) + " (ml)", 1)
        mylcd.lcd_display_string("period: " + str(period[buttonClickCount_period]) + " (min)", 2)
        while True:
            cv.acquire()
            # 버튼이 눌리면
            if GPIO.input(volume_button) == GPIO.LOW:
                while water_do == True:
                    cv.wait()
                print('\t[용량 조절 버튼을 눌렀습니다.]')
                buttonClickCount_volume += 1
                if buttonClickCount_volume >= len(volume):              # 버튼이 5 이상이 되면 다시 원점으로 돌아와야 함
                    buttonClickCount_volume = 0
                    time.sleep(0.5)
                mylcd.lcd_display_string("volume: " + str(volume[buttonClickCount_volume]) + " (ml)", 1)

            if GPIO.input(period_button) == GPIO.LOW:
                while water_do == True:
                    cv.wait()
                print('\t[주기 조절 버튼을 눌렀습니다.]')
                buttonClickCount_period += 1
                if buttonClickCount_period >= len(period):              # 버튼이 4 이상이 되면 다시 원점으로 돌아와야 함
                    buttonClickCount_period = 0
                    time.sleep(0.5)
                mylcd.lcd_display_string("period: " + str(period[buttonClickCount_period]) + " (sec)", 2)

            cv.notify()
            cv.release()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Keyboard Interrupt!!!!")


def func_w():
    global volume
    global period
    global buttonClickCount_period
    global buttonClickCount_volume
    global water_do
    global hx
    p = GPIO.PWM(piezo, 100)
    p.start(100)
    try:
        #print('용량 인덱스: ' +buttonClickCount_volume)
        """
        무게 감지 센서 값 보정
        """
        # 편차에 대한 정보를 담은 파일
        swap_file_name = 'HX711_config.swp'

        # 편차 정보 파일이 존재한다면 그 값을 가져온다.
        if os.path.isfile(swap_file_name):
            with open(swap_file_name, 'rb') as swap_file:
                hx = pickle.load(swap_file)                             # pickle -> 튜플, 리스트, 딕셔너리 등의 객체 자체를 바이너리로 저장
        # 편차 정보 파일이 없다면 생성한다. (HX711 조절)
        else:
            offset = hx.zero()                                          # 기준 무게를 측정하여 편차 값으로 저장한다. (기본적으로 30번의 측정값을 받아 편차를 저장한다.) -> 즉, 영점 조절
            if offset:                                                  # 측정되는 값이 없다면 에러 메세지 띄움.
                raise ValueError('용기 무게를 읽지 못했습니다.')

            raw_reading = hx.get_raw_data_mean()                        # 로드셀 raw data 평균 읽기 (측정값 자체의 평균을 읽어온다. -> 편차가 됨)
            if raw_reading:
                print('로드셀 Raw Data 평균: ', raw_reading)
            else:
                print('로드셀 Raw Data가 유효하지 않음', raw_reading)

            # (측정 값 - 편차)의 평균 -> 반환할 무게
            input('무게를 알고 있는 물체를 올려놓고 Enter를 눌러주세요.\n')
            reading = hx.get_data_mean()
            print('reading 값 : ', reading)
            if reading:
                print('편차를 제외한 Raw Data 평균: ', reading)
                known_weight_grams = input('올려놓은 물체의 무게를 입력 후 Enter를 눌러주세요: ')
                try:
                    value = float(known_weight_grams)
                    print(value, 'grams')
                except ValueError:
                    print('예상 무게: ', known_weight_grams)

                ratio = reading / value                                 # 측정값 /알고있는 값
                hx.set_scale_ratio(ratio)                               # 오차율 저장
                print('Conversion ratio 설정 완료.\n')
            else:
                raise ValueError('평균값 계산 오류. 읽은 값(reading): ', reading)

            # 항상 이 과정을 거치지 않아도 되도록 오차율을 저장한다.
            print('Conversion ratio 값을 HX711_config.swp에 저장')
            with open(swap_file_name, 'wb') as swap_file:
                pickle.dump(hx, swap_file)
                swap_file.flush()
                os.fsync(swap_file.fileno())

        """
        무게 감지 센서, 피에조 및 토양 수분 감지 센서, 워터펌프
        """
        while True:
            val = readChannel(0)

            weight = round(hx.get_weight_mean(20), 1) - 47.2           # get_weight_mean은 보정된 무게들의 평균이다. (소수점 첫째자리까지)
            # time.sleep(3)
            if weight < volume[buttonClickCount_volume]:                # 물이 있어야하는 양만큼 있지 않다면 piezo 센서 울림.
                print("\n\t[물 양이 부족합니다.]")
                print("- 현재 물의 양 : ", max(weight, 0), 'ml')
                for i in range(3):
                    p.ChangeDutyCycle(50)                               # 사용률 50% 로 설정
                    p.ChangeFrequency(330)                              # 주파수 330 으로 설정 (계이름 미에 해당)
                    time.sleep(0.5)
                    p.ChangeDutyCycle(0)
                    time.sleep(0.5)
            else:                                                       # 물이 충분하다면 토양 감지 후 워터펌프 작동
                print("\n\t[물 양이 충분합니다.]")
                print("- 현재 물의 무게 : ", max(weight, 0), 'g')
                if (convertPercent(val) < water_percent_threshold):
                    cv.acquire()
                    water_do = True
                    #print(val, "/", convertPercent(val), "%", "\nhere - [PUMP on]")
                    print("- 현재 토양의 습도 : ", convertPercent(val), "%", "\n- 워터펌프 : ON")

                    GPIO.output(PUMP, 1)
                    time.sleep(volume_sec[buttonClickCount_volume])
                    GPIO.output(PUMP, 0)

                    water_do = False
                    cv.notify()
                    cv.release()
                elif (convertPercent(val) >= water_percent_threshold):
                    #print(water_do)
                    GPIO.output(PUMP, 0)
                    print(val, "/", convertPercent(val), "%", "\nhere - [PUMP off]")
                    print("- 현재 토양의 습도 : ", convertPercent(val), "%", "\n- 워터펌프 : OFF")
                    time.sleep(2)

            #cv.acquire()
            delayTime = period[buttonClickCount_period]
            volumeAmount = volume[buttonClickCount_volume]
            #cv.release()

            #print("주기 인덱스:" + buttonClickCount_period)
            print("- 설정된 용량 : " + str(volumeAmount) + "ml")
            print("- 설정된 주기 : " + str(delayTime) + "초")
            time.sleep(delayTime)

    except KeyboardInterrupt:
        spi.close()
        print("Keyboard Interrupt!!!!")


if __name__ == '__main__':
    try :
        t1 = threading.Thread(target=func_b, args=(), daemon = True)
        t1.start()

        t2 = threading.Thread(target=func_w, args=(), daemon = True)
        t2.start()

        t1.join()
        t2.join()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nKeyboard Interrupt!!!!")
