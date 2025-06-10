from email.header import make_header
import vlc

def make_handler(func, *args):
    """Create a handler function that calls func with args."""
    def handler(event):
        try:
            func(*args, event)
        except Exception as e:
            print(f"Error in handler: {e}")
    return handler

def init_players(self):
    # 공통 옵션을 변수로 선언
    vlc_args = [
        "--no-video-title-show",
        "--avcodec-hw=any",
        "--no-drop-late-frames",
        "--no-skip-frames",
    ]
    # VLC 인스턴스 2개 생성 및 플레이어 리스트 초기화
    self.instances = [vlc.Instance(*vlc_args) for _ in range(2)]
    self.players = [instance.media_player_new() for instance in self.instances]
    # 각 플레이어에 해당하는 위젯에 바인딩
    for idx, player in enumerate(self.players):
        player.set_hwnd(int(self.player_widgets[idx].winId()))
        player.audio_set_volume(100)  # 기본 볼륨 설정
    
def init_players_events(self):
    try:
        for idx, player in enumerate(self.players):
            em = player.event_manager()
            em.event_detach(vlc.EventType.MediaPlayerEndReached)
            em.event_attach(
                vlc.EventType.MediaPlayerEndReached,
                make_handler(self.on_end_reached, idx)
            )
            em.event_attach(
                vlc.EventType.MediaPlayerEncounteredError,
                lambda event, id=idx: self.print("error", f"Player {id} encountered an error.")
            )
            # 이벤트 타입과 핸들러 매핑
            for event_type in [
                vlc.EventType.MediaPlayerTimeChanged,
                vlc.EventType.MediaPlayerPlaying,
                vlc.EventType.MediaPlayerPaused,
                vlc.EventType.MediaPlayerStopped,
                # vlc.EventType.MediaPlayerMediaChanged,
            ]:
                em.event_attach(
                    event_type,
                    make_handler(self.update_player_data, idx)
                )
    except Exception as e:
        self.print("error", f"Error initializing player events: {e}")
        
def update_active_player_id(self, idx):
    self.active_player_id = idx
    self.print("active_player_id", { "value": self.active_player_id })
    
def set_media(self, file, idx):
    """Efficiently set the media for a specific player."""
    if idx < 0 or idx >= len(self.players):
        self.print("error", "Invalid player index provided.")
        return
    if not file:
        self.print("error", "No file provided to set media.")
        return

    media_path = file.get("path", "")
    if not media_path:
        self.print("error", "Invalid media path provided.")
        return

    # Update the current file for the player
    self.current_files[idx] = file

    try:
        if file.get("is_image", True):
            # Efficiently display image
            self.display_image(file, idx)
        else:
            # Only set media if it's different from current
            current_media = self.players[idx].get_media()
            if not current_media or current_media.get_mrl() != media_path:
                media = self.players[idx].get_instance().media_new(media_path)
                self.players[idx].set_media(media)
            self.print('media_changed', { "idx": idx, "uuid": file.get("uuid", ""), "path": media_path })
            self.update_player_data(idx, None)
    except Exception as e:
        self.print("error", f"Error setting media: {e}")
        
def play(self, idx=0):
    """ Play a specific player by index. """
    if self.active_player_id != idx:
        self.update_active_player_id(idx)

    if self.current_files[idx].get("is_image", True):
        # 이미지 재생
        self.display_image(self.current_files[idx], idx)
        return
    else:
        # 미디어 재생
        self.players[idx].play()

    # 해당 플레이어의 위젯이 숨김 상태면 활성화 하기
    if not self.player_widgets[idx].isVisible():
        # 트랜지션(페이드 효과)으로 위젯 전환
        self.fade_transition(idx)

def play_id(self, file):
    """Efficiently play a specific file by ID or path."""
    idx = self.active_player_id

    # Determine next available player index if current is busy
    if self.players[idx].is_playing() or (self.player_widgets[idx].isVisible() and self.player_widgets[idx].pixmap()):
        idx = 1 if idx == 0 else 0
        
    # set Media file for the player
    self.set_media(file, idx)
    self.update_active_player_id(idx)

    try:
        if file.get("is_image") == False:
            self.players[idx].play()
        self.fade_transition(idx)
    except Exception as e:
        self.print("error", f"Error playing file: {e}")

def on_end_reached(self, idx, event):
    """ Handle end reached event for a specific player. """
    try:
        self.update_player_data(idx, event)
        self.print('end_reached', {
            "playlist_track_index": self.track_index,
            "active_player_id": self.active_player_id,
        })
    except Exception as e:
        self.print("error", f"Error handling end reached event: {e}")
        

def pause(self, idx=0):
    """ Pause a specific player by index. """
    if idx < 0 or idx >= len(self.players):
        self.print("error", f"Invalid player index: {idx}")
        return
    self.players[self.active_player_id].pause()
        
def stop(self, idx=None):
    if idx is None:
        idx = self.active_player_id
    """ Stop a specific player by index. """
    if self.current_files[idx].get("is_image", True):
        self.stop_image(idx)
    else :
        self.players[idx].stop()
    self.player_widgets[idx].setVisible(False)  # Hide the player widget
    
def stop_all(self):
    """모든 플레이어와 위젯을 효율적으로 중지하고 로고를 표시합니다."""
    # 모든 플레이어 중지 및 위젯 숨김
    for idx in range(len(self.player_widgets)):
        self.stop(idx)
                
def update_player_data(self, id, event):
    """효율적으로 VLC 플레이어의 상태를 업데이트합니다."""
    try:
        player = self.players[id]
        media = player.get_media()
        data = {
            "id": id,
            "event": str(event.type if event else "None"),
            "media": media.get_mrl() if media else "No media",
            "state": str(player.get_state()),
            "time": player.get_time(),
            "duration": player.get_length(),
            "position": player.get_position(),
            "volume": player.audio_get_volume(),
            "rate": player.get_rate(),
            "is_playing": player.is_playing(),
            "fullscreen": player.get_fullscreen(),
        }
        self.print("player_data", data)
    except Exception as e:
        self.print("error", f"Error updating player data: {e}")