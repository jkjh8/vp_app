import vlc

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
    self.print("debug", "Initialized VLC players with double instances")
    
def init_players_events(self):
    try:
        def make_handler(method, idx):
            return lambda event: method(idx, event)
        for idx, player in enumerate(self.players):
            em = player.event_manager()
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
                vlc.EventType.MediaPlayerMediaChanged,
            ]:
                em.event_attach(
                    event_type,
                    make_handler(self.update_player_data, idx)
                )
    except Exception as e:
        self.print("error", f"Error initializing player events: {e}")
        
def update_active_player_id(self, idx):
    self.active_player_id = idx
    self.print("active_player_id", { "id": self.active_player_id })
        
def stop(self, idx=None):
    if idx is None:
        idx = self.active_player_id
    """ Stop a specific player by index. """
    if self.current_files[idx].get("is_image", True):
        self.stop_image(idx)
    else :
        self.players[idx].stop()
    self.player_widgets[idx].setVisible(False)  # Hide the player widget
    self.print("debug", f"Player {idx} stopped.")
    
def set_time(self, time, idx=None):
    """효율적으로 특정 플레이어의 재생 시간을 설정합니다."""
    idx = self.active_player_id if idx is None else idx

    if not isinstance(time, int) or time < 0:
        self.print("error", "Invalid time value provided.")
        return

    try:
        self.players[idx].set_time(time)
        self.print("debug", f"Set player {idx} time to: {time}")
    except Exception as e:
        self.print("error", f"Error setting time for player {idx}: {e}")
    
    
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