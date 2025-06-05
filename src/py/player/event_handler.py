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
        # "show_logo": lambda data: set_logo_visibility(self, data.get("show", True)),
        # "logo_file": lambda data: set_logo_file(self, data.get("file", "")),
        # "logo_size": lambda data: set_logo_size(self, data.get("width", 0), data.get("height", 0)),
        "playid": lambda data: self.play_id(data.get("file", {})),
        "playlist_mode": lambda data: self.set_playlist_mode(data.get("value", False)),
    }
    func = dispatch.get(command)
    if func:
        try:
            func(data)
        except Exception as e:
            self.print("error", f"Error executing command '{command}': {e}")
    else:
        self.print("error", f"Unknown command: {command}")