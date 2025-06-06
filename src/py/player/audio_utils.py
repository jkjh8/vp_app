import vlc

def set_audio_device(self, device_id):
    """Set the audio output device for all players."""
    try:
        for player in self.players:
            player.audio_output_device_set(None, device_id)
        self.print("debug", f"Setting audio output device to: {device_id}")
    except Exception as e:
        self.print("error", f"Error setting audio device: {e}")


def get_audio_devices(self):
    """Return a list of available audio devices for a VLC player."""
    try:
        devices = []
        for player in self.players:
            if not player:
                self.print("error", {"message": "VLC player not initialized."})
                continue

            dev_list = player.audio_output_device_enum()
            if dev_list:
                dev = dev_list
            while dev:
                dev_info = dev.contents
                devices.append({
                    "deviceid": dev_info.device.decode() if dev_info.device else "default",
                    "name": dev_info.description.decode() if dev_info.description else "기본 장치"
                })
                dev = dev_info.next
        self.print("audiodevices", {"devices": devices})
        return devices
    except Exception as e:
        self.print("error", {"message": f"Error getting audio devices: {e}"})
        return []
