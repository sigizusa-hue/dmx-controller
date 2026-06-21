import time
import threading
from pyftdi.ftdi import Ftdi

# V2: longer break (1200 baud = ~8ms low) so it's clearly visible on scope
# and slower frame rate (10Hz) so the break gap is unmistakable
BREAK_BAUD     = 1200
DMX_BAUD       = 250_000
MAB_DURATION   = 50e-6    # 50us MAB - more visible on scope
FRAME_INTERVAL = 1 / 10   # 10Hz - slow enough to see frame gaps clearly

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
        print(f"[DMX v2] Driver started -> {self._url}")
        print("[DMX v2] Break baud: 1200 (~8ms break), Frame rate: 10Hz")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        try:
            self._ftdi.close()
        except Exception:
            pass
        print("[DMX v2] Driver stopped.")

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

    def _send_break(self):
        self._ftdi.set_baudrate(BREAK_BAUD)
        self._ftdi.write_data(bytes([0x00]))
        self._ftdi.set_baudrate(DMX_BAUD)
        time.sleep(MAB_DURATION)

    def _frame_loop(self):
        frame_count = 0
        t_report = time.monotonic()
        while self._running:
            t_start = time.monotonic()
            self._send_break()
            with self._lock:
                packet = bytes([0x00]) + bytes(self._buffer)
            self._ftdi.write_data(packet)
            elapsed = time.monotonic() - t_start
            sleep_for = FRAME_INTERVAL - elapsed
            if sleep_for > 0:
                time.sleep(sleep_for)
            frame_count += 1
            if frame_count % 10 == 0:
                now = time.monotonic()
                fps = 10 / (now - t_report)
                t_report = now
                print(f"[DMX v2] Frame rate: {fps:.1f} Hz  (target 10 Hz)")
