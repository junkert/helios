import spidev
import time
from pprint import pprint

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 40000000
num_leds = 160


def fill(r, g, b):
    for led in range(0, num_leds):
        buff[led][0] = gamma[g]
        buff[led][1] = gamma[r]
        buff[led][2] = gamma[b]


def update():
    final_buf = []
    for i in range(num_leds):
        final_buf.append(buff[i][0])
    final_buf.append(0)
    spi.xfer(final_buf)

gamma = bytearray(256)
buff = [0 for x in range(num_leds)]

for led in range(num_leds):
    buff[led] = bytearray(3)

for i in range(256):
    # Color calculations from
    # http://learn.adafruit.com/light-painting-with-raspberry-pi
    gamma[i] = 0x80 | int(pow(float(i) / 255.0, 2.5) * 127.0 + 0.5)

fill(0, 0, 0)
update()

while True:
    for i in range(0, 256, 1):
        fill(i, i, i)
        update()
        time.sleep(0.001)
    for i in range(255, -1, -1):
        fill(i, i, i)
        update()
        time.sleep(0.001)
