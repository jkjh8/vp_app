from PySide6.QtCore import QThread, Signal
import sys

class stdinReaderr(QThread):
    message_received = Signal(str)
    def __init__(self):
        super().__init__()
        self.running = True
        self.receive_udp_data = ""

    def run(self):
        while self.running:
            try:
                if self.running == False:
                    break
                data = sys.stdin.readline()
                if data:
                    self.receive_udp_data = data.strip()
                    self.message_received.emit(self.receive_udp_data)
            except Exception as e:
                self.print_json("error", {"message": f"Error reading stdin: {e}"})
                break

    def stop(self):
        self.running = False