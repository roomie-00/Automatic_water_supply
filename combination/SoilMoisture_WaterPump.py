import RPi.GPIO as GPIO
import signal
import sys
import time
import spidev

delay = 2


def signal_handler(signal, frame):
  print('process stop')
  GPIO.cleanup()
  sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

GPIO.setmode(GPIO.BCM)

PUMP = 12

GPIO.setup(PUMP, GPIO.OUT)
# Open Spi Bus
# SPI 버스 0과 디바이스 0을 열고
# 최대 전송 속도를 1MHz로 설정
spi = spidev.SpiDev()
spi.open(0,0) # open(bus, device)
spi.max_speed_hz = 1000000 # set transfer speed

# To read SPI data from MCP3008 chip
# Channel must be 0~7 integer
def readChannel(channel):
  val = spi.xfer2([1, (8+channel)<<4, 0])
  data = ((val[1]&3) << 8) + val[2]
  return data

# 0~1023 value가 들어옴. 1023이 수분함량 min값
def convertPercent(data):
  return 100.0-round(((data*100)/float(1023)),1)

try:
  while True:
    val = readChannel(0)
    # if (val != 0) : # filtering for meaningless num
    #   print(val, "/", convertPercent(val),"%")
    # time.sleep(delay)
    if (convertPercent(val) < 10):
      print(val, "/", convertPercent(val), "%", "\nhere - PUMP on")
      #GPIO.output(PUMP, 1)
      #time.sleep(2)
      #GPIO.output(PUMP, 0)
      #time.sleep(delay)
    elif(convertPercent(val) >= 10):
      #GPIO.output(PUMP, 0)
      print(val, "/", convertPercent(val), "%", "\nhere - PUMP off")
      time.sleep(2)
except KeyboardInterrupt:
  spi.close()
  print("Keyboard Interrupt!!!!")