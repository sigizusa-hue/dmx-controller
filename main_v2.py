import time
from dmx_driver_v2 import DmxDriver

def main():
    driver = DmxDriver()
    try:
        driver.start()
        ch1_value = 255
        driver.set_channel(1, ch1_value)
        print(f"[MAIN v2] Channel 1 = {ch1_value}")
        print("[MAIN v2] Press ENTER to toggle Ch1. Ctrl-C to quit.")
        while True:
            try:
                input()
            except EOFError:
                time.sleep(1)
                continue
            ch1_value = 0 if ch1_value == 255 else 255
            driver.set_channel(1, ch1_value)
            print(f"[MAIN v2] Channel 1 -> {'FULL' if ch1_value == 255 else 'STANDBY'}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        driver.stop()

if __name__ == "__main__":
    main()
