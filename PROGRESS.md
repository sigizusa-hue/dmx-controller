# DMX Controller - Progress Notes

## Milestone 1 - COMPLETE
Generate a valid, continuously-refreshed DMX signal that the dimmer recognizes.

### Hardware
- Raspberry Pi 4 (aarch64), Node v22, Python 3
- ENTTEC Open DMX USB (FTDI FT232R, non-isolated, dumb variant)
- Hantek oscilloscope for signal verification
- Dimmer confirmed responding to signal consistently

### Working Configuration
- python main.py -- 40Hz, dimmer recognizes signal consistently (USE THIS)
- python main_v2.py -- 10Hz, dimmer loses signal intermittently (too slow)

### Key Lessons Learned

1. set_break() does NOT work on FT232R via pyftdi
   USB control transfer latency is too high. Generate break by switching
   to low baud rate (57600) and sending 0x00. One byte at 57600 = ~174us,
   well above the DMX 88us minimum.

2. RTS polarity is ACTIVE LOW on the ENTTEC Open DMX USB
   RS-485 transceiver DE pin is tied to RTS. DE is active-low:
     set_rts(False) = RS-485 output ENABLED
     set_rts(True)  = RS-485 output DISABLED
   Discovered via test_rts.py toggling RTS while watching scope.

3. Pi setup after every reboot:
     sudo rmmod ftdi_sio usbserial
   Kernel reloads FTDI serial driver on boot. Errors = fine (not loaded).

4. pyftdi install (one-time):
     pip install pyftdi --break-system-packages

### Deploy Workflow
1. Edit code in Codespace
2. git push origin main
3. Pi: cd ~/dmx-controller && git pull && python main.py

### Repo
sigizusa-hue/dmx-controller (public for now, lock down later)
TODO: set up SSH key auth on Pi, make repo private

### Scope Verification
- Signal confirmed at 100us/div on Hantek
- Break visible as long low pulse before each data burst
- Amplitude matches proper DMX controller reference
- Frame rate: ~39.9Hz steady

### Remote Monitoring
- DroidCam on Android -> http://192.168.101.46:4747/video
- Chrome extension screenshots scope feed live
- Full feedback loop: scope -> Claude sees it -> fixes code -> push -> pull

## Milestone 2 - TODO
- [x] Confirm ch1=255 drives dimmer to full brightness
- [x] blink.py: ch1 toggles 0/255 at 2Hz, dimmer LED visibly blinks
- [ ] Mock driver (logs instead of USB, for Codespace testing)
- [ ] Controller layer (scenes, sequences)
- [ ] Flask remote-monitoring dashboard
