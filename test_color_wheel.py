import time
import math
sleep_time = 0.001
frequency = 0.075
for i in range(0, (2**8)):
    r = int(math.sin(frequency*i + 0) * 127 + 128)
    g = int(math.sin(frequency*i + 2) * 127 + 128)
    b = int(math.sin(frequency*i + 4) * 127 + 128)
    print "%d: [%d, %d, %d]" % (i, r, g, b)
    time.sleep(sleep_time)