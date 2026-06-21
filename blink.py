import time
from dmx_driver import DmxDriver
driver = DmxDriver()
driver.start()
print("[BLINK] Ch1 blinking 2x/sec. Ctrl-C to stop.")
try:
    while True:
        driver.set_channel(1, 255)
        time.sleep(0.5)
        driver.set_channel(1, 0)
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    driver.stop()
