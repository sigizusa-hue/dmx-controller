from pyftdi.ftdi import Ftdi
import time
f = Ftdi()
f.open_from_url('ftdi://ftdi:232r/1')
f.reset()
time.sleep(0.05)
f.set_line_property(8,2,'N')
f.set_flowctrl('')
f.set_baudrate(250000)
print('Looping - Ctrl-C to stop')
try:
    while True:
        print('RTS=False, DTR=False...')
        f.set_rts(False)
        f.set_dtr(False)
        f.write_data(bytes([0x00]+[0xFF]*512))
        time.sleep(3)
        print('RTS=True, DTR=True...')
        f.set_rts(True)
        f.set_dtr(True)
        f.write_data(bytes([0x00]+[0xFF]*512))
        time.sleep(3)
except KeyboardInterrupt:
    print('Done.')
f.close()
