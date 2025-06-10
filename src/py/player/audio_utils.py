import vlc
import time
import threading

def set_audio_device_with_retry(self, device_id, retry_interval=2, max_retries=3):
    """Set the audio output device with retry logic."""
    def retry_logic():
        retries = 0
        while retries < max_retries:
            self.set_audio_device(device_id)
            if self.set_audio_device_result:
                self.print("debug", f"Audio device successfully set to: {device_id}")
                return
            self.print("warn", f"Retrying to set audio device: {device_id} (Attempt {retries + 1}/{max_retries})")
            retries += 1
            time.sleep(retry_interval)
        self.print("error", f"Failed to set audio device after {max_retries} attempts.")

    # Run the retry logic in a separate thread to avoid blocking
    threading.Thread(target=retry_logic).start()

def set_audio_device(self, device_id):
    """Set the audio output device for all players."""
    try:
        for player in self.players:
            result = player.audio_output_device_set(None, device_id if device_id else None)
            # 성공 조건: result가 None 또는 0일 경우
            if result is not None and result != 0:
                self.print("error", f"Failed to set audio device: {device_id}. VLC returned: {result}")
                self.set_audio_device_result = False
                return
        self.set_audio_device_result = True
        self.print("debug", f"Audio device successfully set to: {device_id}")
    except Exception as e:
        self.print("error", f"Error setting audio device: {e}")
        self.set_audio_device_result = False

def get_audio_devices(self):
    """Return a list of available audio devices for a VLC player."""
    try:
        devices = []
        player = self.players[0] if self.players else vlc.MediaPlayer()
        if not player:
            self.print("error", "No player available to get audio devices.")
            return []
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
