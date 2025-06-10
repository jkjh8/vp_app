import json
import time


# 명령 처리 함수
def handle_stdin_message(self, data):
    """ Handle commands received from stdin. """
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        self.print("error", "Invalid JSON received from stdin")
        return
    command = data.get("command")
    if not isinstance(command, str):
        self.print("error", f"Invalid command type: {type(command)}. Expected a string.")
        return
    # 짧은 시간 내 중복 메시지 필터링
    current_time = time.time()
    if not hasattr(self, 'last_command_time'):
        self.last_command_time = {}
    last_time = self.last_command_time.get(command, 0)
    if current_time - last_time < 0.1:  # 0.5초 이내 중복 메시지 무시
        self.print("debug", f"Skipping duplicate command within short interval: {command}")
        return
    self.last_command_time[command] = current_time
    # 명령어에 따라 적절한 함수 호출
    dispatch = {
        # logo
        "show_logo": lambda data: self.set_logo_visibility(data.get("show", True)),
        "logo_file": lambda data: self.set_logo_file(data.get("file", "")),
        "logo_size": lambda data: self.set_logo_size(int(data.get("size", 0))),
        # player
        "set_media": lambda data: self.set_media(data.get("file", {}), int(data.get("idx", 0))),
        "playid": lambda data: self.play_id(data.get("file", {})),
        "play": lambda data: self.play(int(data.get("idx", 0))),
        "pause": lambda data: self.pause(int(data.get("idx", 0))),
        "stop": lambda data: self.stop(int(data.get("idx", 0))),
        "stop_all": lambda data: self.stop_all(),
        # audio devices
        "set_audio_device": lambda data: self.set_audio_device(data.get("device_id", "")),
        "get_audio_devices": lambda data: self.get_audio_devices(),
        # playlist
        "playlist_mode": lambda data: self.set_playlist_mode(bool(data.get("value", False))),
        "playlist_play": lambda data: self.playlist_play(int(data.get("idx", 0))),
        "set_tracks": lambda data: self.set_tracks(data.get("tracks", [])),
        "image_time": lambda data: self.set_image_time(int(data.get("time", 0))),
        "set_track_index": lambda data: self.update_track_index(int(data.get("index", 0))),
        "next": lambda data: self.next(),
        "previous": lambda data: self.previous(),
        "set_time": lambda data: self.set_time(int(data.get("time", 0)), int(data.get("idx", 0))),
        # etc
        "set_fullscreen": lambda data: self.set_fullscreen(data.get("value", False)),
        "background_color": lambda data: self.set_background_color(data.get("color", "#000000")),
    }
    func = dispatch.get(command)
    if func:
        try:
            if command == "set_track_index":
                pass
            func(data)
        except Exception as e:
            self.print("error", f"Error executing command '{command}': {e}")
    else:
        self.print("error", f"Unknown command: {command}")