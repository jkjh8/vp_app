import os, io, sys, json, threading, time, vlc, win32process, win32con
import tkinter as tk
from tkinter import ttk
import asyncio

# 표준 입출력 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

last_command_time = {}

def print_json(type, data):
    """json 포맷으로 로그 출력"""
    print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)

def stdin_read():
    while True:
        try:
            data = sys.stdin.readline().strip()
            if data:
                handle_stdin_message(data)
        except Exception as e:
            print_json("error", f"Error reading stdin: {str(e)}")
            break

def handle_stdin_message(data):
        """표준입력으로 들어오는 명령 처리"""
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print_json("error", "Invalid JSON received from stdin")
            return
        command = data.get("command")
        if not isinstance(command, str):
            print_json("error", f"Invalid command type: {type(command)}. Expected a string.")
            return
        # 짧은 시간 내 중복 메시지 필터링
        current_time = time.time()
        global last_command_time
        if last_command_time is None:
            last_command_time = {}
        last_time = last_command_time.get(command, 0)
        if current_time - last_time < 0.1:  # 0.5초 이내 중복 메시지 무시
            print_json("debug", f"Skipping duplicate command within short interval: {command}")
            return
        last_command_time[command] = current_time
        # 명령어에 따라 적절한 함수 호출
        dispatch = {
            # # logo
            # "show_logo": lambda data: self.set_logo_visibility(data.get("show", True)),
            # "logo_file": lambda data: self.set_logo_file(data.get("file", "")),
            # "logo_size": lambda data: self.set_logo_size(int(data.get("size", 0))),
            # # player
            # "set_media": lambda data: self.set_media(data.get("file", {}), int(data.get("idx", 0))),
            # "playid": lambda data: self.play_id(data.get("file", {})),
            # "play": lambda data: self.play(int(data.get("idx", 0))),
            # "pause": lambda data: self.pause(int(data.get("idx", 0))),
            # "stop": lambda data: self.stop(int(data.get("idx", 0))),
            # "stop_all": lambda data: self.stop_all(),
            # # audio devices
            # "set_audio_device": lambda data: self.set_audio_device(data.get("device_id", "")),
            # "get_audio_devices": lambda data: self.get_audio_devices(),
            # # playlist
            # "playlist_mode": lambda data: self.set_playlist_mode(bool(data.get("value", False))),
            # "playlist_play": lambda data: self.playlist_play(int(data.get("idx", 0))),
            # "set_tracks": lambda data: self.set_tracks(data.get("tracks", [])),
            # "image_time": lambda data: self.set_image_time(int(data.get("time", 0))),
            # "set_track_index": lambda data: self.update_track_index(int(data.get("index", 0))),
            # "next": lambda data: self.next(),
            # "previous": lambda data: self.previous(),
            # "set_time": lambda data: self.set_time(int(data.get("time", 0)), int(data.get("idx", 0))),
            # # etc
            # "set_fullscreen": lambda data: self.set_fullscreen(data.get("value", False)),
            "background_color": lambda data: player.set_background_color(data.get("color", "#000000")),
        }
        func = dispatch.get(command)
        if func:
            try:
                if command == "set_track_index":
                    pass
                func(data)
            except Exception as e:
                print_json("error", f"Error executing command '{command}': {e}")
        else:
            print_json("error", f"Unknown command: {command}")

class Player:
    def __init__(self, pstatus=None, app_path=None):
        self.root = tk.Tk()
        self.pstatus = pstatus
        self.app_path = app_path
        # print 함수 재정의
        self.print = lambda type, data: print_json(type, data)
        # 초기화
        self.player_frame = None
        self.background_color = pstatus.get("background_color", "#000000")

        self.print("info", f"Player initialized with pstatus and app_path={self.pstatus}, {self.app_path}.")
        
    def set_background_color(self, color):
        """배경색 설정"""
        self.background_color = color
        self.player_frame.configure(bg=self.background_color)
        self.print("info", f"Background color set to {self.background_color}.")

    def initUI(self):
        self.root.title("Media Player")
        self.root.geometry("800x600")

        # 플레이어 프레임 생성
        self.player_frame = tk.Frame(self.root, bg=self.background_color)
        self.player_frame.pack(fill=tk.BOTH, expand=True)

        # ico 설정
        icon_path = os.path.join(self.app_path,"src", "icon.ico") if self.app_path else None
        if icon_path and os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        else:
            self.print("warn", f"Icon file not found at {icon_path}. Using default icon.")


if __name__ == "__main__":
    vp_pstatus_json = json.loads(os.environ.get("VP_PSTATUS")) if os.environ.get("VP_PSTATUS") else {}
    app_path = os.environ.get("APP_PATH")
    stdio = threading.Thread(target=stdin_read, daemon=True)
    stdio.start()
    player = Player(pstatus=vp_pstatus_json, app_path=app_path)
    player.initUI()
    player.root.mainloop()