import time
from engine import Engine

engine = Engine()
engine.load()
engine.play('program1')
engine.start()

print('[MAIN] Engine running. TCP commands on port 5555.')
print('[MAIN] Commands: PLAY program1 | PLAY program2 | STOP | RELOAD | STATUS')
print('[MAIN] Ctrl-C to quit.')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    engine.driver.stop()
    print('[MAIN] Done.')
