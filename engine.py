import socket
import threading
from program_reader import load_programs
from clock import Clock
from dmx_driver import DmxDriver

TCP_HOST = '0.0.0.0'
TCP_PORT = 5555

class Engine:
    def __init__(self):
        self.driver = DmxDriver()
        self.programs = {}
        self.current_program = None
        self.current_steps = {}
        self.step_count = 0
        self._lock = threading.Lock()

    def load(self, programs_path='data/programs.csv', clock_path='data/clock.txt'):
        self.programs = load_programs(programs_path)
        self.clock = Clock.from_file(self._on_step, clock_path)
        print(f'[Engine] Loaded {len(self.programs)} programs: {list(self.programs.keys())}')

    def play(self, program_id):
        with self._lock:
            if program_id not in self.programs:
                print(f'[Engine] Unknown program: {program_id}')
                return
            self.current_program = program_id
            self.current_steps = self.programs[program_id]
            self.step_count = len(self.current_steps)
            print(f'[Engine] Playing {program_id} ({self.step_count} steps)')

    def stop_program(self):
        with self._lock:
            self.current_program = None
            for ch in range(1, 513):
                self.driver.set_channel(ch, 0)
            print('[Engine] Stopped, all channels zeroed')

    def reload(self):
        self.programs = load_programs()
        print(f'[Engine] Reloaded programs: {list(self.programs.keys())}')

    def _on_step(self, step):
        with self._lock:
            if not self.current_program:
                return
            step_idx = ((step - 1) % self.step_count) + 1
            channels = self.current_steps.get(step_idx, {})
            for ch, val in channels.items():
                self.driver.set_channel(ch, val)

    def start(self):
        self.driver.start()
        self.clock.start()
        self._start_tcp()
        print(f'[Engine] TCP listening on {TCP_HOST}:{TCP_PORT}')

    def _start_tcp(self):
        t = threading.Thread(target=self._tcp_server, daemon=True)
        t.start()

    def _tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((TCP_HOST, TCP_PORT))
            s.listen(5)
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self._handle, args=(conn, addr), daemon=True).start()

    def _handle(self, conn, addr):
        print(f'[TCP] Connected: {addr}')
        with conn:
            for line in conn.makefile():
                cmd = line.strip()
                if not cmd:
                    continue
                print(f'[TCP] Command: {cmd}')
                parts = cmd.split()
                if parts[0] == 'PLAY' and len(parts) > 1:
                    self.play(parts[1])
                    conn.sendall(b'OK\n')
                elif parts[0] == 'STOP':
                    self.stop_program()
                    conn.sendall(b'OK\n')
                elif parts[0] == 'RELOAD':
                    self.reload()
                    conn.sendall(b'OK\n')
                elif parts[0] == 'STATUS':
                    conn.sendall(f'program={self.current_program}\n'.encode())
                else:
                    conn.sendall(b'ERR unknown command\n')
        print(f'[TCP] Disconnected: {addr}')
