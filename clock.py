import time
import threading

def load_clock(path='data/clock.txt'):
    cfg = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if '=' in line:
                k, v = line.split('=', 1)
                cfg[k.strip()] = float(v.strip())
    return cfg

class Clock:
    def __init__(self, on_step, step_duration=0.5, offset=0):
        self.on_step = on_step
        self.step_duration = step_duration
        self.offset = offset
        self._running = False
        self._thread = None

    @classmethod
    def from_file(cls, on_step, path='data/clock.txt'):
        cfg = load_clock(path)
        return cls(on_step,
                   step_duration=cfg.get('step_duration', 0.5),
                   offset=cfg.get('offset', 0))

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f'[Clock] Started: step={self.step_duration}s offset={self.offset}s')

    def stop(self):
        self._running = False

    def _run(self):
        if self.offset > 0:
            time.sleep(self.offset)
        step = 1
        while self._running:
            self.on_step(step)
            step += 1
            time.sleep(self.step_duration)
