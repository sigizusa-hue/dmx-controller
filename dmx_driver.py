import time
import threading
from pyftdi.ftdi import Ftdi

BREAK_BAUD     = 57600
DMX_BAUD       = 250_000
MAB_DURATION   = 12e-6
FRAME_INTERVAL = 1 / 40

class DmxDriver:
    def __init__(self, url="ftdi://ftdi:232r/1"):
        self._url = url
        self._buffer = bytearray(512)
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._ftdi = Ftdi()

    def set_channel(self, channel, value):
        if not (1 <= channel <= 512):
            raise ValueError(f"Channel must be 1-512, got {channel}")
        if not (0 <= value <= 255):
            raise ValueError(f"Value must be 0-255, got {value}")
        with self._lock:
            self._buffer[channel - 1] = value

    def start(self):
        self._open_device()
        self._running = True
        self._thread = threading.Thread(target=self._frame_loop, daemon=True)
        self._thread.start()
        print(f"[DMX] Driver started -> {self._url}")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        try:
            self._ftdi.close()
        except Exception:
            pass
        print("[DMX] Driver stopped.")

    def _open_device(self):
        self._ftdi.open_from_url(self._url)
        self._ftdi.reset()
        time.sleep(0.05)
        self._ftdi.set_line_property(8, 2, "N")
        self._ftdi.set_flowctrl("")
        self._ftdi.set_rts(False)
        self._ftdi.set_dtr(False)
        self._ftdi.set_baudrate(DMX_BAUD)
        self._ftdi.purge_buffers()
        time.sleep(0.05)
        print("[DMX] Device opened and reset.")

    def _reopen_device(self):
        """Attempt to recover the FTDI device after a USB error."""
        try:
            self._ftdi.close()
        except Exception:
            pass
        time.sleep(0.2)
        try:
            self._open_device()
            print("[DMX] Device recovered after error.")
            return True
        except Exception as e:
            print(f"[DMX] Recovery failed: {e}")
            return False

    def _send_break(self):
        self._ftdi.set_baudrate(BREAK_BAUD)
        self._ftdi.write_data(bytes([0x00]))
        self._ftdi.set_baudrate(DMX_BAUD)
        time.sleep(MAB_DURATION)

    def _frame_loop(self):
        frame_count = 0
        error_count = 0
        t_report = time.monotonic()
        while self._running:
            t_start = time.monotonic()
            try:
                self._send_break()
                with self._lock:
                    packet = bytes([0x00]) + bytes(self._buffer)
                self._ftdi.write_data(packet)
                error_count = 0
            except Exception as e:
                error_count += 1
                print(f"[DMX] Frame error #{error_count}: {e}")
                if self._reopen_device():
                    error_count = 0
                else:
                    time.sleep(0.5)
                continue

            elapsed = time.monotonic() - t_start
            sleep_for = FRAME_INTERVAL - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
            frame_count += 1
            if frame_count % 100 == 0:
                now = time.monotonic()
                fps = 100 / (now - t_report)
                t_report = now
                print(f"[DMX] Frame rate: {fps:.1f} Hz  (target 40 Hz)")
