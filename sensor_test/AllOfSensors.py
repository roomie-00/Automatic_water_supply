import RPi.GPIO as GPIO
import signal
import sys
import time
import spidev
# 버튼 관련
import I2C_LCD_driver


# 키보드 인터럽트 걸리면 빠져 나오는 용도
def signal_handler(signal, frame):
  print('process stop')
  GPIO.cleanup()
  sys.exit(0)

 
signal.signal(signal.SIGINT, signal_handler)

GPIO.setmode(GPIO.BCM) # BCM 모드

## 토양 수분 + 워터펌프 관련 세팅 시작 ##
PUMP = 12 # 워터펌프 핀
delay = 2 # 주기 설정된 것 넣을 곳
GPIO.setup(PUMP, GPIO.OUT) # 워터펌프 물 나오게

# Open Spi Bus
# SPI 버스 0과 디바이스 0을 열고
# 최대 전송 속도를 1MHz로 설정
spi = spidev.SpiDev()
spi.open(0,0) # open(bus, device)
spi.max_speed_hz = 1000000 # set transfer speed

# 임계값
water_percent_threshold = 10

# To read SPI data from MCP3008 chip
# Channel must be 0~7 integer
def readChannel(channel):
  val = spi.xfer2([1, (8+channel)<<4, 0])
  data = ((val[1]&3) << 8) + val[2]
  return data

# 0~1023 value가 들어옴. 1023이 수분함량 min값
def convertPercent(data):
  return 100.0-round(((data*100)/float(1023)),1)

## 토양 수분 + 워터펌프 관련 세팅 끝 ##

## 주기 조절 버튼 + 용량 조절 버튼 + LCD 표시 세팅 시작 ##
mylcd = I2C_LCD_driver.lcd()

LCD = 2 # LCD 핀은 라즈베리파이 GPIO 2번핀으로
volume_button = 15
GPIO.setup(volume_button, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# 스위치 핀을 풀다운저항이 있는 출력으로 설정
# 풀다운 저항이 있으면 버튼을 누르지 않으면 LOW 신호가 됨
# 여기를 GPIO.PUD_UP으로 하면 버튼을 누르지 않으면 HIGH 신호가 됨

period_button = 6; # 주기 버튼 GPIO핀 달기
GPIO.setup(period_button, GPIO.IN, pull_up_down = GPIO.PUD_UP)

volume = ["100 (ml)", "150 (ml)", "200 (ml)", "250 (ml)"]
period = ["01 (min)", "10 (min)", "20 (min)", "30 (min)"]
buttonClickCount_volume = 0 # 0, 1, 2, 3 인덱스 참조용
buttonClickCount_period = 0 # 0, 1, 2 인덱스 참조용

# 주기 조절 버튼 P 눌렀을 때 주기 조절
def period_button_callback(signal, frame):
    print('주기 조절 버튼 누름')
    # 눌렀을 때
    buttonClickCount_period += 1
    if buttonClickCount_period >= len(period):
         # 버튼이 4 이상이 되면 다시 원점으로 돌아와야 함
        buttonClickCount_period = 0
        time.sleep(0.5)
        
    mylcd.lcd_display_string(" period: " + period[buttonClickCount_period], 2)

# 용량 조절 버튼 V 눌렀을 때 용량 조절
def volume_button_callback(signal, frame):
    print('용량 조절 버튼 누름')
    buttonClickCount_volume += 1
    if buttonClickCount_volume >= len(volume):
         # 버튼이 4 이상이 되면 다시 원점으로 돌아와야 함
        buttonClickCount_volume = 0
        time.sleep(0.5)
    mylcd.lcd_display_string("volume: " + volume[buttonClickCount_volume], 1)




# 이벤트 핸들러 달기
GPIO.add_event_detect(period_button, GPIO.FALLING, callback=volume_button_callback)
GPIO.add_event_detect(period_button, GPIO.FALLING, callback=period_button_callback)


## 주기 조절 버튼 + 용량 조절 버튼 세팅 + LCD 표시 세팅 끝 ##
try:
  while True:
    mylcd.lcd_display_string("volume: " + volume[buttonClickCount_volume], 1)
    mylcd.lcd_display_string(" period: " + period[buttonClickCount_period], 2)
    val = readChannel(0)
    # if (val != 0) : # filtering for meaningless num
    #   print(val, "/", convertPercent(val),"%")
    # time.sleep(delay)
    if (convertPercent(val) < water_percent_threshold):
      print(val, "/", convertPercent(val), "%", "\nhere - PUMP on")
      GPIO.output(PUMP, 1)
      time.sleep(2)
      GPIO.output(PUMP, 0)
      time.sleep(delay)
    elif(convertPercent(val) >= water_percent_threshold):
      GPIO.output(PUMP, 0)
      print(val, "/", convertPercent(val), "%", "\nhere - PUMP off")
      time.sleep(2)
except KeyboardInterrupt:
  spi.close()
  print("Keyboard Interrupt!!!!")