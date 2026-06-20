"""
dmx_driver.py — ENTTEC Open DMX USB driver via pyftdi.

DMX512 framing (per frame):
  1. Break:            line held LOW  >= 88us  (we use ~100us)
  2. Mark-after-break: line held HIGH >= 8us   (we use ~12us)
  3. Start code 0x00 + 512 channel bytes at 250000 baud, 8N2

Frame rate target: ~40 Hz (25ms per frame)

Exposes:
  set_channel(channel, value)  — channel 1-512, value 0-255
  start() / stop()             — control the background thread
"""

import time
import threading
from pyftdi.ftdi import Ftdi


BREAK_DURATION = 100e-6   # 100 us  (spec minimum 88 us)
MAB_DURATION   =  12e-6   # 12 us   (spec minimum 8 us)
FRAME_INTERVAL =  1 / 40  # 25 ms   -> ~40 Hz


class DmxDriver:
    """
    Drives an ENTTEC Open DMX USB (FTDI FT232R) to output a continuous
    DMX512 signal.  The Open DMX has no onboard intelligence, so we handle
    the break/MAB manually by toggling the FTDI UART break condition.
    """

    def __init__(self, url: str = "ftdi://ftdi:232r/1"):
        self._url = url
        self._buffer = bytearray(512)
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._ftdi = Ftdi()

    def set_channel(self, channel: int, value: int) -> None:
        """Set a DMX channel (1-512) to value (0-255)."""
        if not (1 <= channel <= 512):
            raise ValueError(f"Channel must be 1-512, got {channel}")
        if not (0 <= value <= 255):
            raise ValueError(f"Value must be 0-255, got {value}")
        with self._lock:
            self._buffer[channel - 1] = value

    def start(self) -> None:
        """Open the FTDI device and begin the DMX frame loop."""
        self._open_device()
        self._running = True
        self._thread = threading.Thread(target=self._frame_loop, daemon=True)
        self._thread.start()
        print(f"[DMX] Driver started -> {self._url}")

    def stop(self) -> None:
        """Stop the frame loop and release the FTDI device."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        try:
            self._ftdi.close()
        except Exception:
            pass
        print("[DMX] Driver stopped.")

    def _open_device(self) -> None:
        self._ftdi.open_from_url(self._url)
        self._ftdi.set_baudrate(250_000)
        self._ftdi.set_line_property(8, 2, "N")
        self._ftdi.set_flowctrl("")
        self._ftdi.set_break(False)

    def _frame_loop(self) -> None:
        frame_count = 0
        t_report = time.monotonic()

        while self._running:
            t_frame_start = time.monotonic()

            # 1. Break (~100 us)
            self._ftdi.set_break(True)
            time.sleep(BREAK_DURATION)

            # 2. Mark-after-break (~12 us)
            self._ftdi.set_break(False)
            time.sleep(MAB_DURATION)

            # 3. Start code + 512 channel bytes
            with self._lock:
                packet = bytes([0x00]) + bytes(self._buffer)
            self._ftdi.write_data(packet)

            # 4. Pace to ~40 Hz
            elapsed = time.monotonic() - t_frame_start
            sleep_for = FRAME_INTERVAL - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)

            # 5. Report frame rate every 100 frames
            frame_count += 1
            if frame_count % 100 == 0:
                now = time.monotonic()
                fps = 100 / (now - t_report)
                t_report = now
                print(f"[DMX] Frame rate: {fps:.1f} Hz  (target 40 Hz)")
