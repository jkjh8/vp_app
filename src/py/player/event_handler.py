import json


# 명령 처리 함수
def handle_stdin_message(self, data):
    """ Handle commands received from stdin. """
    self.print("debug", f"Received data from stdin: {data}")
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        self.print("error", "Invalid JSON received from stdin")
        return
    command = data.get("command")
    if not isinstance(command, str):
        self.print("error", f"Invalid command type: {type(command)}. Expected a string.")
        return
    # 명령어에 따라 적절한 함수 호출
    dispatch = {
        # logo
        "show_logo": lambda data: self.set_logo_visibility(data.get("show", True)),
        "logo_file": lambda data: self.set_logo_file(data.get("file", "")),
        "logo_size": lambda data: self.set_logo_size(int(data.get("size", 0))),
        # player
        "playid": lambda data: self.play_id(data.get("file", {})),
        "play": lambda data: self.play(int(data.get("idx", 0))),
        "pause": lambda data: self.pause(int(data.get("idx", 0))),
        "stop": lambda data: self.stop(int(data.get("idx", 0))),
        "stop_all": lambda data: self.stop_all(),
        "set_time": lambda data: self.set_time(data.get("time", 0), data.get("idx", 0)),
        # audio devices
        "set_audio_device": lambda data: self.set_audio_device(data.get("device_id", "")),
        "get_audio_devices": lambda data: self.get_audio_devices(),
        # playerlist
        "playlist_mode": lambda data: self.set_playlist_mode(data.get("value", False)),
        # etc
        "set_fullscreen": lambda data: self.set_fullscreen(data.get("value", False)),
        "background_color": lambda data: self.set_background_color(data.get("color", "#000000")),
    }
    func = dispatch.get(command)
    if func:
        try:
            func(data)
        except Exception as e:
            self.print("error", f"Error executing command '{command}': {e}")
    else:
        self.print("error", f"Unknown command: {command}")