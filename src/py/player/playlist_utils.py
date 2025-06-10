def set_playlist_mode(self, value):
    """ Set the playlist mode (on/off). """
    self.print("debug", f"Setting playlist mode to: {value}")
    self.playlist_mode = value
    
def set_tracks(self, tracks):
    """ Set the playlist tracks efficiently. """
    if not isinstance(tracks, list):
        self.print("error", "Invalid tracks format, expected a list.")
        return

    self.tracks = tracks
        
def update_track_index(self, idx):
    """ Update the current track index. """
    if idx < 0 or idx >= len(self.tracks):
        self.print("error", f"Invalid track index: {idx}")
        return
    self.track_index = idx
    self.print("track_index", { "value": self.track_index })

def playlist_play(self, idx = 0):
    # self.print("error", f"Playlist play called with index: {idx}")
    """ Play the current track in the playlist. """
    if idx is not None:
        if idx < 0 or idx >= len(self.tracks):
            self.print("error", f"Invalid playlist index: {idx}")
            return
        self.update_track_index(idx)
    if not self.tracks or self.track_index >= len(self.tracks):
        self.print("error", "Playlist is empty or index out of range.")
        return

    file = self.tracks[self.track_index]
    self.play_id(file)
    # set next track load next player
    self.next_file_load()
    self.image_timer()
        
def next(self):
    if not self.playlist_mode:
        self.print("error", "Next track can only be used in playlist mode.")
        return

    if self.image_timer_instance.isActive():
        self.image_timer_instance.stop()
        self.print("debug", "Existing image timer stopped.")

    if not self.current_files[self.next_player_index].get("is_image"):
        self.players[self.next_player_index].play()

    self.fade_transition(self.next_player_index)
    self.track_index = self.next_track_index  # Update track_index for image playback
    self.update_track_index(self.track_index)
    self.next_file_load()
    self.image_timer()
    
def previous(self):
    """ 이전 트랙으로 이동합니다. """
    if not self.playlist_mode:
        self.print("error", "Previous track can only be used in playlist mode.")
        return
    
    if self.players[self.active_player_id].get_time() > 5000:
        self.players[self.active_player_id].set_time(0)
        return

    if self.image_timer_instance.isActive():
        self.image_timer_instance.stop()
        self.print("debug", "Existing image timer stopped.")

    # 이전 트랙 인덱스 계산
    self.track_index -= 1
    if self.track_index < 0:
        self.track_index = len(self.tracks) - 1
    
    self.playlist_play(self.track_index)
        
def next_file_load(self, idx=None):
    """ Load the next file in the playlist. """
    self.print("warn", f"Current track index: {self.track_index}, Next track index: {self.next_track_index}")

    if idx is not None:
        self.next_track_index = idx
    else:
        self.next_track_index = self.track_index + 1

    if self.next_track_index >= len(self.tracks):
        self.next_track_index = 0

    self.next_player_index = 1 if self.active_player_id == 0 else 0
    self.set_media(self.tracks[self.next_track_index], self.next_player_index)
    # self.print("debug", f"Updated next track index to: {self.next_track_index}")
    
def set_time(self, time, idx=None):
    """효율적으로 특정 플레이어의 재생 시간을 설정합니다."""
    idx = self.active_player_id if idx is None else idx

    if not isinstance(time, int) or time < 0:
        self.print("error", "Invalid time value provided.")
        return

    try:
        self.players[idx].set_time(time)
    except Exception as e:
        self.print("error", f"Error setting time for player {idx}: {e}")
        
def image_timer(self):
    """ 플레이 리스트 모드에서 이미지 재생 시 타이머를 설정합니다. """
    # 기존 타이머 중지 및 안전한 신호 해제
    if self.image_timer_instance.isActive():
        self.image_timer_instance.stop()
        try:
            self.image_timer_instance.timeout.disconnect()
            self.print("debug", "Existing image timer stopped and disconnected.")
        except RuntimeError:
            self.print("debug", "Timeout signal was not connected, skipping disconnect.")

    if not self.playlist_mode:
        self.print("error", "Image timer can only be set in playlist mode.")
        return

    if not self.tracks or self.track_index >= len(self.tracks):
        self.print("debug", "Playlist is empty or index out of range.")
        return

    if not self.current_files[self.active_player_id].get("is_image", False):
        self.print("debug", "Current file is not an image, skipping image timer setup.")
        return

    self.image_timer_instance.start(self.image_time * 1000)
    self.print("debug", f"Image timer started for {self.image_time} seconds.")