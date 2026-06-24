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

## Milestone 2 - IN PROGRESS

### Architecture (built)
Modular engine controlled over the network, decoupled from the driver:

```
data/programs.csv  -> [program_reader] -> programs in memory
data/clock.txt     -> [Clock]          -> fires step events at interval
                      [Engine]          -> current program + step, writes to driver
                      [TCP server :5555]-> receives PLAY/STOP/RELOAD/STATUS
                      [DmxDriver]       -> hardware
```

### Files added
- program_reader.py -- parses programs.csv (ProgramID,StepNo,ChannelNo,ChannelVal)
- clock.py -- Clock class, fires on_step callback every step_duration; reads data/clock.txt
- engine.py -- Engine ties it together + TCP command server on port 5555
- main_engine.py -- entry point: loads, plays program1, starts engine + TCP
- data/programs.csv -- program definitions (program1, program2)
- data/clock.txt -- step_duration, offset config

### TCP control (real-time, language-agnostic, works over WiFi)
Send commands from any machine on the network:
  echo "PLAY program1" | nc -w1 192.168.1.109 5555
  echo "PLAY program2" | nc -w1 192.168.1.109 5555
  echo "STOP"          | nc -w1 192.168.1.109 5555
  echo "STATUS"        | nc -w1 192.168.1.109 5555
NOTE: use TCP not UDP. nc -u (UDP) will NOT work - server is TCP.
Engine prints "[TCP] Command: <cmd>" on receipt. "Disconnected" after is normal.

### Windows -> Pi startup (start_pi.bat)
A .bat on Windows SSHes into the Pi, starts a tmux session, frees the FTDI
device, pulls latest code, and runs the engine. Keep 'pause' at the end so the
window stays open. Straight ssh -t works better than routing through PowerShell.
  @echo off
  ssh -t p4@192.168.1.109 "tmux kill-session -t dmx 2>/dev/null; tmux new-session -d -s dmx -c /home/p4/dmx-controller; tmux send-keys -t dmx:0.0 'sudo rmmod ftdi_sio usbserial 2>/dev/null; git pull && python main_engine.py' C-m; tmux attach -t dmx"
  pause
TODO: SSH key auth so no password prompt each time.

### Driver resilience (added)
Hit a "pyftdi.ftdi.FtdiError: UsbError: [Errno 32] Pipe error" during continuous
operation - the frame loop thread crashed while the engine kept running (DMX
went dark but TCP still worked). dmx_driver.py now wraps the frame loop in
try/except: on USB error it prints the error, tries to reopen/recover the FTDI
device, and continues instead of dying. Watch for frequency - if frequent, may
need to revisit baud-switch break timing or USB power.

### Workflow lessons
- Codespace -> GitHub -> Pi requires BOTH halves: gcp (push) on Codespace AND
  git pull on Pi. The autostart bat does the pull automatically on launch.
- gcp alias on Codespace: git add -A && git commit -m update && git push
- If gcp is rejected (diverged history), the Codespace had commits GitHub didn't,
  AND GitHub had a commit the Codespace didn't. Fix: git pull (merge), resolve
  any conflict, push. Clicking Sync does pull+push but won't auto-resolve conflicts.
- Edit programs.csv directly in the Codespace browser editor (small file, fine).

## Milestone 2 - REMAINING TODO
- [ ] Mock driver (logs instead of USB, so Codespace can run engine without hardware)
- [ ] Program switcher trigger logic (when/how to auto-switch programs)
- [ ] Flask remote-monitoring dashboard
- [ ] Test program switching live on the dimmer
- [ ] SSH key auth on Pi (no password)
