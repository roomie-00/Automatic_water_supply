import RPi.GPIO as GPIO
import time
import spidev

# Moter Drive 연결 PIN => 우리가 직접 연결 후 맞는지 확인 필요
A1A = 5
A1B = 6

# 습도 임계치(%)
HUM_THRESHOLD = 20 # 임의로 20%로 해둠

# 센서를 물에 담갔을 때의 토양습도 센서의 출력 값
HUM_MAX = 0

# 초기 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(A1A, GPIO.OUT) #출력으로
GPIO.output(A1A, GPIO.LOW) #일단 LOW로

GPIO.setup(A1B, GPIO.OUT) #출력으로
GPIO.output(A1B, GPIO.LOW) #일단 LOW로

spi = spidev.SpiDev()
spi.open(0,0)

# ADC값을 가져오는 함수 (아날로그 값을 디지털 값으로 읽는 것)
# 수업시간에 한 것처럼 아날로그를 디지털로
def read_spi_adc(adcChannel):
  adcValue = 0
  buff = spi.xfer2([1, (8 + adcChannel) << 4, 0])
  adcValue = ((buff[1]&3) << 8) + buff[2]
  return adcValue


# 센서 값을 백분율로 변환하기 위한 map 함수
def map(value, min_adc, max_adc, min_hum, max_hum):
  adc_range = max_adc - min_adc
  hum_range = max_hum - min_hum
  scale_factor = float(adc_range) / float(hum_range)
  return min_hum + ((value - min_adc) / scale_factor)

try:
  adcChannel = 0
  while True:
    adcValue = read_spi_adc(adcChnnel)
    # 가져온 데이터를 % 단위로 변환, 습도가 높을수록 낮은 값을 반환하므로
    # 100에서 빼주어 습도가 높을 수록 백분율이 높아지도록 계산
    # 우리가 보기 편하게 해주는 부분임
    hum = 100 - int(map(adcValue, HUM_MAX, 1023, 0, 100))
    if hum < HUM_TRHESHOLD:
      # 임계치보다 수분값이 작으면, 이 부분은 우리가 실험 후 임계값 다시 설정
      GPIO.output(A1A, GPIO.HIGH) # 워터펌프 가동 
      GPIO.output(A1B, GPIO.LOW) 
    else:
      GPIO.output(A1A, GPIO.LOW)
      GPIO.output(A1B, GPIO.LOW) 
    
    time.sleep(0.5) # 0.5초 간 급수 이 부분도 어느정도로 할지 1초에 몇 ml 나오는지 확인 후 정하기
    # 다시 꺼주기
    GPIO.output(A1A, GPIO.LOW)
    GPIO.output(A1B, GPIO.LOW) 
    time.sleep(60) # 60초 = 1분에 1번씩 검사하도록 = 사실 실제로는 30분마다 1번씩해도 충분함. 시연을 위해서 일단 1분으로 설정
except KeyboardInterrupt:
  print("종료")
finally:
  GPIO.cleanup()
  spi.close()

