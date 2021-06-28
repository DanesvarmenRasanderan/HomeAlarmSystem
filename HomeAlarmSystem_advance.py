
#Created by : Danesvarmen Rasanderan

from machine import Pin, UART
import utime
from gpio_lcd import GpioLcd


ok = 0
err = 0
n = 20

#----------Details-----------
SSID = "XXXXXXXXXXXXXXX"
Password = "XXXXXXXXXXXXXXX"
base_url = "https://api.thingspeak.com/apps/thinghttp/send_request?api_key=XXXXXXXX"
ThingspeakAPI = "XXXXXXXXXXXXXXX"
#-----------------------------

# Initialize Pin
buzzer = Pin(0, Pin.OUT)
motionSensor = Pin(28, Pin.IN)
LedOn = Pin(3, Pin.OUT)
resetSw = Pin(18, Pin.IN)
relay = Pin(2, Pin.OUT)
led_onboard = Pin(25, Pin.OUT)

uart0 = UART(0, rx=Pin(17), tx=Pin(16), baudrate=115200)
print(uart0)

lcd = GpioLcd(rs_pin=Pin(8),
              enable_pin=Pin(9),
              d4_pin=Pin(10),
              d5_pin=Pin(11),
              d6_pin=Pin(12),
              d7_pin=Pin(13),
              num_lines=2, num_columns=16)

# Initialize value
LedOn.value(1)
relay.value(0)

# custom characters

lock = bytearray([0x0E,0x11,0x11,0x1F,0x1B,0x1B,0x1F,0x00])
unlock = bytearray([0x0E,0x11,0x10,0x10,0x1F,0x1B,0x1B,0x1F])
bell = bytearray([0x04,0x04,0x0E,0x0E,0x0E,0x1F,0x04,0x00])
bellR = bytearray([0x04,0x04,0x0E,0x0E,0x0E,0x1F,0x04,0x02])
bellL = bytearray([0x04,0x04,0x0E,0x0E,0x0E,0x1F,0x04,0x08])
wave3 = bytearray([0x08,0x04,0x02,0x01,0x01,0x02,0x04,0x08])
wave2 = bytearray([0x00,0x08,0x04,0x02,0x02,0x04,0x08,0x00])
wave1 = bytearray([0x00,0x00,0x08,0x04,0x04,0x08,0x00,0x00])


def waveMove():
    lcd.clear()
    lcd.move_to(1,0)
    lcd.custom_char(0, wave1)
    lcd.putchar(chr(0))
    utime.sleep(0.1)
    lcd.clear()
    lcd.move_to(2,0)
    lcd.custom_char(0, wave2)
    lcd.putchar(chr(0))
    utime.sleep(0.1)
    lcd.clear()
    lcd.move_to(3,0)
    lcd.custom_char(0, wave3)
    lcd.putchar(chr(0))
    utime.sleep(0.1)


def blinkLEDOnboard():       # onboard LED OFF/ON for 0.1/0.1 sec
    led_onboard.value(0)
    utime.sleep(0.1)
    led_onboard.value(1)
    utime.sleep(0.1)
    led_onboard.value(0)


def sendCMD_waitResp(cmd, uart=uart0, timeout=2000):
    print("CMD: " + cmd)
    uart.write(cmd)
    waitResp(uart, timeout)
    print()

def waitResp(uart=uart0, timeout=2000):
    global ok
    global err
    prvMills = utime.ticks_ms()
    resp = b""
    while (utime.ticks_ms()-prvMills)<timeout:
        if uart.any():
            resp = b"".join([resp, uart.read(1)])
    print("resp:")
    try:
        print(resp.decode())
        blinkLEDOnboard()
        ok=ok+1
    except UnicodeError:
        print(resp)
        err=err+1


def initializeESP01():                                                                    # The timeout=x can be adjusted
    sendCMD_waitResp("AT\r\n", timeout=3000)                                              # Test AT startup
    sendCMD_waitResp("AT+CWMODE=1\r\n")                                                   # Set the Wi-Fi mode = Station mode
    sendCMD_waitResp("AT+CWJAP={},{}\r\n".format(SSID, Password), timeout=5000)           # Connect to AP
    sendCMD_waitResp("AT+CIPMUX=0\r\n", timeout=1000)
    sendCMD_waitResp("AT+CIPMUX=1\r\n", timeout=1000)


def submitdataESP01():

    sendCMD_waitResp("AT+CIPSTART=3,\"TCP\",\"api.thingspeak.com\",80\r\n", timeout=5000)


    Http = ("GET /apps/thinghttp/send_request?api_key={}".format(ThingspeakAPI) + "\r\n")

    HttpLen = len(Http)

    sendCMD_waitResp("AT+CIPSEND=3," + str(HttpLen) + "\r\n" , timeout=5000)
    sendCMD_waitResp(Http , timeout=100)
    sendCMD_waitResp("\r\n", timeout=1000)

    print('Messega send to ThingHttp-twilio')


def pwmtimer(dc, f):

    timeall = 1/f         # Calculate frequency

    t1 = timeall*(dc/100) # Calculate t1
    t2 = timeall - t1     # Calculate t2

    t1 = int(t1*1000000)  # convert and calculate t1 in interger
    t2 = int(t2*1000000)  # convert and calculate t2 in interger

    buzzer.high()         # Turn ON Buzzer
    utime.sleep_us(t1)    # Delay
    buzzer.low()          # Turn OFF Buzzer
    utime.sleep_us(t2)    # Delay


def callBuzzer():

    fstart = 1000
    fstop = 2000
    fstep = 2

    for j in range (fstart, fstop, fstep):
        pwmtimer(50,j)

    for j in reversed (range (fstart, fstop, fstep)):
        pwmtimer(50,j)


def action(pin):
    print()
    print("Motion Is Detected!!!")
    lcd.clear()
    lcd.move_to(4,0)
    lcd.putstr("Motion")
    lcd.move_to(2,1)
    lcd.putstr("Detected!!")
    relay.value(1)
    submitdataESP01()
    state = 1
    while state == 1:

        if resetSw.value() == 1:
            LedOn.value(0)
            callBuzzer()
        else:
            relay.value(0)
            LedOn.value(1)
            lcd.clear()
            lcd.custom_char(0, lock)
            lcd.putchar(chr(0))
            lcd.move_to(5,0)
            lcd.putstr("Alarm")
            lcd.move_to(2,1)
            lcd.putstr("deactivated!!")
            print()
            print("Alarm deactivated!!")
            state = 0


initializeESP01()
lcd.move_to(4,0)
lcd.putstr("System")
lcd.move_to(4,1)
lcd.putstr("Running")
motionSensor.irq(trigger = Pin.IRQ_RISING, handler = action)

while True:
    motionSensor.irq(trigger = Pin.IRQ_RISING, handler = action)
    utime.sleep(1)
