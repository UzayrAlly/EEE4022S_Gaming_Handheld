import time
import spidev
import RPi.GPIO as GPIO
import uinput

#Initial Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#GPIO Pin definitions
buttons = {
    "BTN_SOUTH": 17,   # A 
    "BTN_EAST": 27,    # B 
    "BTN_NORTH": 22,  # Y 
    "BTN_WEST": 26,   # X 
    "BTN_SELECT": 23,  # Select
    "BTN_START": 24,   # Start
    "BTN_TL": 25,     # L1
    "BTN_TR": 16,     # R1
    "BTN_R3": 5,     #R3
    "BTN_L3": 6      #L3
 }

# Set up GPIO as inputs with pull-ups
for pin in buttons.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# SPI setup 
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

#Reading MCP
def read_adc(channel):
    if not 0 <= channel <= 7:
        return 0
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) | adc[2]
    return data
#Virtual Gamepad for Detection by Steam
events = [
    uinput.BTN_SOUTH, uinput.BTN_EAST,
      uinput.BTN_NORTH, uinput.BTN_WEST,
    uinput.BTN_SELECT, uinput.BTN_START,
      uinput.BTN_TL, uinput.BTN_TR,
      uinput.BTN_R3, uinput.BTN_L3,
    uinput.ABS_X + (0, 1023, 0, 0),
    uinput.ABS_Y + (0, 1023, 0, 0),
    uinput.ABS_RX + (0, 1023, 0, 0),
    uinput.ABS_RY + (0, 1023, 0, 0),
    uinput.ABS_Z + (0, 1023, 0, 0),
    uinput.ABS_RZ + (0, 1023, 0, 0),
    uinput.ABS_HAT0X + (-1, 1, 0, 0),
    uinput.ABS_HAT0Y + (-1, 1, 0, 0),
]

device = uinput.Device(events, name="PiController")

#Normalise ADC readings
def normalise(value):
    return max(0, min(1023, value))

try:
    while True:
        #Read Joysticks
        lx = normalise(read_adc(0))  # Left X
        ly = normalise(read_adc(1))  # Left Y
        rx = normalise(read_adc(2))  # Right X
        ry = normalise(read_adc(3))  # Right Y

        #Triggers
        lt_val = normalise(read_adc(4))
        rt_val = normalise(read_adc(5))

        #Joystick Positions
        device.emit(uinput.ABS_X, lx)
        device.emit(uinput.ABS_Y, ly)
        device.emit(uinput.ABS_RX, rx)
        device.emit(uinput.ABS_RY, ry)
        device.emit(uinput.ABS_Z, lt_val)
        device.emit(uinput.ABS_RZ, rt_val)
        

        # Buttons
        for name, pin in buttons.items():
            pressed = not GPIO.input(pin)  # LOW = pressed (because of pull-up)
            device.emit(getattr(uinput, name), int(pressed))

        # D-pad
        hat_x = 0
        hat_y = 0
        if not GPIO.input(16):  # LEFT
            hat_x = -1
        elif not GPIO.input(12):  # RIGHT
            hat_x = 1
        if not GPIO.input(26):  # UP
            hat_y = -1
        elif not GPIO.input(9):  # DOWN
            hat_y = 1
        device.emit(uinput.ABS_HAT0X, hat_x)
        device.emit(uinput.ABS_HAT0Y, hat_y)

        time.sleep(0.01)

except KeyboardInterrupt:
    GPIO.cleanup()
    spi.close()
    print("Controller stopped.")