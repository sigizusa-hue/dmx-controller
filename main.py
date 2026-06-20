"""
main.py -- Milestone 1 test harness for the DMX controller.

Starts the DMX frame loop with channel 1 set to 255 (full).
Press ENTER to toggle channel 1 between 0 (standby) and 255 (full).
Press Ctrl-C to quit.
"""

import sys
import time
from dmx_driver import DmxDriver


def main():
    driver = DmxDriver()

    try:
        driver.start()

        ch1_value = 255
        driver.set_channel(1, ch1_value)
        print(f"[MAIN] Channel 1 = {ch1_value}")
        print("[MAIN] Press ENTER to toggle Ch1 between 0 and 255.")
        print("[MAIN] Press Ctrl-C to quit.\n")

        while True:
            try:
                input()
            except EOFError:
                time.sleep(1)
                continue

            ch1_value = 0 if ch1_value == 255 else 255
            driver.set_channel(1, ch1_value)
            label = "FULL (255)" if ch1_value == 255 else "STANDBY (0)"
            print(f"[MAIN] Channel 1 -> {label}")

    except KeyboardInterrupt:
        print("\n[MAIN] Ctrl-C received, stopping...")
    finally:
        driver.stop()
        print("[MAIN] Done.")


if __name__ == "__main__":
    main()
