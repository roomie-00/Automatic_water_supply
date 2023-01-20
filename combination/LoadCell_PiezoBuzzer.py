import RPi.GPIO as GPIO
from hx711 import HX711             # hx711
import pickle
import os
import time

# 로드셀 센서 제어
GPIO.setmode(GPIO.BCM)
# 핀번호 DT(20) -> 센서 데이터 신호 / SCK(16) -> 센서 제어용 신호
hx = HX711(dout_pin = 20, pd_sck_pin = 16)

# Piezo 센서 제어
piezo = 26     # 핀번호 미정

GPIO.setup(piezo, GPIO.OUT) #출력
p = GPIO.PWM(piezo, 100)
p.start(100)
try :
    # 편차에 대한 정보를 담은 파일
    swap_file_name = 'HX711_config.swp'

    # 편차 정보 파일이 존재한다면 그 값을 가져온다.
    if os.path.isfile(swap_file_name) :
        with open(swap_file_name, 'rb') as swap_file:
            hx = pickle.load(swap_file)                                 # pickle -> 튜플, 리스트, 딕셔너리 등의 객체 자체를 바이너리로 저장
    # 편차 정보 파일이 없다면 생성한다. (HX711 조절)
    else :
        # 기준 무게를 측정하여 편차 값으로 저장한다. (기본적으로 30번의 측정값을 받아 편차를 저장한다.) -> 즉, 영점 조절
        offset = hx.zero()
        # 측정되는 값이 없다면 에러 메세지 띄움.
        if offset :
            raise ValueError('용기 무게를 읽지 못했습니다.')

        # 로드셀 raw data 평균 읽기 (측정값 자체의 평균을 읽어온다. -> 편차가 됨)
        raw_reading = hx.get_raw_data_mean()
        if raw_reading :
            print('로드셀 Raw Data 평균값: ', raw_reading)
        else :
            print('로드셀 Raw Data가 유효하지 않음', raw_reading)

        # (측정 값 - 편차)의 평균 -> 반환할 무게
        input('무게를 알고 있는 물체를 올려놓고 Enter를 눌러주세요.\n')
        reading = hx.get_data_mean()
        print('여기까지는 돌아가나요?')
        print('reading 값 : ', reading)
        if reading:
            print('Offset 값을 제외한 Raw Data 평균값: ', reading)
            known_weight_grams = input('올려놓은 물체의 무게를 입력 후 Enter를 눌러주세요: ')
            try:
                value = float(known_weight_grams)
                print(value, 'grams')
            except ValueError:
                print('예상 무게: ', known_weight_grams)

            ratio = reading / value                                     # 측정값/알고있는 값
            hx.set_scale_ratio(ratio)                                   # 오차율 저장
            print('Conversion ratio 설정 완료.\n')
        else:
            raise ValueError('평균값 계산 오류. 읽은 값(reading): ', reading)

        # 항상 이 과정을 거치지 않아도 되도록 오차율을 저장한다.
        print('Conversion ratio 값을 HX711_config.swp에 저장')
        with open(swap_file_name, 'wb') as swap_file:
            pickle.dump(hx, swap_file)
            swap_file.flush()
            os.fsync(swap_file.fileno())
    while True:
        # 피에조와의 연결 부분
        weight = round(hx.get_weight_mean(), 1)                           # get_weight_mean은 보정된 무게들의 평균이다. (소수점 첫째자리까지)

        if weight < 100 :                                                 # 기준값 아직 미정 대충 100g (= 100ml) 로 설정했습니다.
            weight = round(hx.get_weight_mean(20), 1)
            print(max(weight,0), 'g')
            for i in range(3) :
               p.ChangeDutyCycle(50)                                     # 사용률 50% 로 설정
               p.ChangeFrequency(330)                                    # 주파수 330 으로 설정 (계이름 미에 해당)
               time.sleep(0.5)
               p.ChangeDutyCycle(0)
               time.sleep(0.5)




    # ## 무게 값 출력 예제 (테스트용)
    # print("무게 측정을 멈출려면 'CTRL + C'를 눌러주세요.")
    # input('Enter를 눌러서 무게 측정 시작!\n')
    # while True:
    #     weight = round(hx.get_weight_mean(20), 1)
    #     print(max(weight,0), 'g')

finally:
    p.stop()
    GPIO.cleanup()
