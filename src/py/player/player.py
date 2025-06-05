import os, sys, json, vlc, win32process, win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from stdin import stdinReaderr
from background import set_background_color
from event_handler import handle_stdin_message

class Player(QMainWindow):
    def __init__(self, pstatus=None):
        """ Initialize the media player with the given status. """
        super().__init__()
        self.setWindowTitle("Media Player")
        self.setGeometry(100, 100, 800, 600)
        
        try:
            win32process.SetPriorityClass(win32process.GetCurrentProcess(), win32con.REALTIME_PRIORITY_CLASS)
            self.print("info", "Process priority set to REALTIME")
        except Exception as e:
            self.print("error", f"Failed to initialize stdin reader: {e}")
        # stdin reader for receiving commands
        self.stdin_reader = stdinReaderr()
        self.stdin_reader.message_received.connect(lambda: handle_stdin_message(self, self.stdin_reader.receive_udp_data))
        self.stdin_reader.start()
        
        # 파비콘 설정
        icon_path = os.path.abspath("src/py/player/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            self.print("info", f"Icon set from {icon_path}")
        else:
            self.print("error", f"Warning: Icon file not found at {icon_path}")

        # 초기 변수 지정
        self.pstatus = pstatus  # Store pstatus for later use
        self.playlist_mode = bool(self.pstatus.get("playlistMode", False))  # 플레이리스트 모드 여부
        self.playlist = []
        self.playlist_track_index = int(self.pstatus.get("playlistTrackIndex", 0))
        self.audio_devices = []
        self.image_time = int(self.pstatus.get("imageTime", 10))
        self.logo_file = self.pstatus.get("logo", {}).get("file", "")
        self.logo_show = bool(self.pstatus.get("logo", {}).get("show", True))
        self.logo_height = int(self.pstatus.get("logo", {}).get("height", 100))
        self.logo_width = int(self.pstatus.get("logo", {}).get("width", 100))
        self.logo_svg = self.logo_file.lower().endswith(".svg")  # SVG 로고 여부
        self.background_color = self.pstatus.get("background", "#000000")
        self.active_player_id = 0
        self.print("active_player_id", { "id": self.active_player_id })
        # 3개의 위젯 생성
        self.player_widget_1 = QLabel(self)  # 현재 동작 중인 위젯
        self.player_widget_2 = QLabel(self)  # 대기 위젯
        self.logo_widget = QLabel(self)  # 로고 위젯
        self.player_widgets = [self.player_widget_1, self.player_widget_2]
        # 배경색 지정
        set_background_color(self, self.background_color)
        # 위젯 크기를 MainWindow에 가득 차게 설정
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())

        # 현재 동작 중인 위젯 및 대기 위젯 초기화
        for player in self.player_widgets:
            player.setVisible(False)  # 초기에는 숨김
        # 로고 위젯 초기화 복원
        if self.logo_file:
            self.print("debug", f"Attempting to load logo file: {self.logo_file}")
            if self.logo_svg:
                try:
                    self.logo_widget = QSvgWidget(self.logo_file, self)
                    self.print("debug", "SVG logo widget initialized successfully.")
                except Exception as e:
                    self.print("error", f"Failed to initialize SVG logo widget: {e}")
            else:
                try:
                    pixmap = QPixmap(self.logo_file)
                    if not pixmap.isNull():
                        self.logo_widget.setPixmap(pixmap.scaled(self.logo_width, self.logo_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        self.print("debug", "Pixmap logo widget initialized successfully.")
                    else:
                        self.print("error", "Pixmap is null. Failed to load image.")
                except Exception as e:
                    self.print("error", f"Failed to initialize Pixmap logo widget: {e}")

            # 로고 위젯의 크기와 위치를 중앙으로 설정
            logo_x = (self.width() - self.logo_width) // 2
            logo_y = (self.height() - self.logo_height) // 2
            self.logo_widget.setGeometry(logo_x, logo_y, self.logo_width, self.logo_height)
            self.logo_widget.setVisible(self.logo_show)
            self.print("debug", f"Logo widget visibility set to: {self.logo_show}")

        # 로고 파일 경로 확인
        if not self.logo_file:
            self.print("error", "Logo file path is empty.")
            return

        if not os.path.exists(self.logo_file):
            self.print("error", f"Logo file does not exist: {self.logo_file}")
            return

        self.print("debug", f"Logo file exists: {self.logo_file}")

        # 로고 위젯 초기화 상태 확인
        if self.logo_svg:
            self.print("debug", "Attempting to initialize SVG logo widget.")
        else:
            self.print("debug", "Attempting to initialize Pixmap logo widget.")

        # VLC 플레이어 초기화
        self.init_players()
        self.get_audio_devices()  # 오디오 디바이스 목록 가져오기
        self.set_audio_device(self.pstatus.get("device", {}).get("audiodevice", "default"))  # 오디오 디바이스 설정
    
    def init_players(self):
        self.instanceA = vlc.Instance("--no-video-title-show",
        "--avcodec-hw=any",
        "--no-drop-late-frames",
        "--no-skip-frames")
        self.instanceB = vlc.Instance("--no-video-title-show",
        "--avcodec-hw=any",
        "--no-drop-late-frames",
        "--no-skip-frames")
        self.playerA = self.instanceA.media_player_new()
        self.playerB = self.instanceB.media_player_new()
        self.players = [self.playerA, self.playerB]
        # 각각의 winId를 사용하여 동일한 창에 표시되도록 설정
        self.playerA.set_hwnd(int(self.player_widgets[0].winId()))
        self.playerB.set_hwnd(int(self.player_widgets[1].winId()))
        self.print("debug", "Initialized VLC players with double instances")
    
    def init_players_events(self):
        try:
            for player, idx in enumerate(self.players):
                em = player.event_manager()
                em.event_attach(
                    vlc.EventType.MediaPlayerEndReached,
                    lambda event, id=idx: self.on_end_reached(id, event)
                )
                em.event_attach(
                    vlc.EventType.MediaPlayerEncounteredError,
                    lambda event, id=idx: self.print("error", f"Player {id} encountered an error.")
                )
                em.event_attach(
                    vlc.EventType.MediaPlayerTimeChanged,
                    lambda event, id=idx: self.update_player_data(id, event)
                )
                em.event_attach(
                    vlc.EventType.MediaPlayerPlaying,
                    lambda event, id=idx: self.update_player_data(id, event)
                )
                em.event_attach(
                    vlc.EventType.MediaPlayerPaused,
                    lambda event, id=idx: self.update_player_data(id, event)
                )
                em.event_attach(
                    vlc.EventType.MediaPlayerStopped,
                    lambda event, id=idx: self.update_player_data(id, event)
                )
                em.event_attach(
                    vlc.EventType.MediaPlayerMediaChanged,
                    lambda event, id=idx: self.update_player_data(id, event)
                )
        except Exception as e:
            self.print("error", f"Error initializing player events: {e}")
    

    def set_playlist_mode(self, value):
        """ Set the playlist mode (on/off). """
        self.print("debug", f"Setting playlist mode to: {value}")
        self.playlist_mode = value
    
    def play_id(self, file):
        """ Play a specific file by ID or path. """
        if not file:
            self.print("error", "No file provided to play.")
            return

        media_path = file.get("path", "")
        if not media_path:
            self.print("error", "Invalid media path provided.")
            return

        self.print("debug", f"Playing file: {media_path}")
        try:
            media = self.players[self.active_player_id].get_instance().media_new(media_path)
            self.players[self.active_player_id].set_media(media)
            self.players[self.active_player_id].play()
            self.player_widgets[self.active_player_id].setVisible(True)  # 현재 플레이어 위젯 보이기
        except Exception as e:
            self.print("error", f"Error playing file: {e}")

    def on_end_reached(self, idx, event):
        """ Handle end reached event for a specific player. """
        self.print("info", f"Player {idx} has reached the end.")
        self.update_player_data(idx, event)
        self.print('end_reached', { "playlist_track_index": self.playlist_track_index, "active_player_id": self.active_player_id, "id": idx })

    def update_player_data(self, id, event):
        """ VLC 플레이어의 상태를 업데이트합니다. """
        self.print("player_data", {
            "id": id,
            "state": self.players[id].get_state(),
            "time": self.players[id].get_time(),
            "duration": self.players[id].get_length(),
            "position": self.players[id].get_position(),
            "volume": self.players[id].audio_get_volume(),
            "rate": self.players[id].get_rate(),
            "is_playing": self.players[id].is_playing(),
            "fullscreen": self.players[id].get_fullscreen(),
        })
        
    def set_audio_device(self, device_id):
        try:
            for player in self.players:
                player.audio_output_device_set(None, device_id)
            self.print("debug", f"Setting audio output device to: {device_id}")
        except Exception as e:
            self.print("error", f"Error setting audio device: {e}")
            return
        
    def get_audio_devices(self):
        """ VLC에서 사용 가능한 오디오 디바이스 목록을 반환합니다. """
        try:
            devices = []
            if not self.players[self.active_player_id]:
                
                self.print("error", {"message": "VLC player not initialized."})
                return
            dev_list = self.players[self.active_player_id].audio_output_device_enum()
            if dev_list:
                dev = dev_list
                while dev:
                    dev_info = dev.contents
                    devices.append({
                        "deviceid": dev_info.device.decode() if dev_info.device else "default",
                        "name": dev_info.description.decode() if dev_info.description else "기본 장치"
                    })
                    dev = dev_info.next
            self.print("audiodevices", { "devices": devices })
        except Exception as e:
            self.print("error", {"message": f"Error getting audio devices: {e}"})

    def print(self, type, data):
        """ Print the function name and data in a formatted way. """
        print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)

    def fade_transition(self, from_widget, to_widget):
        """ 페이드 효과로 위젯 전환 """
        # from_widget에 QGraphicsOpacityEffect 추가
        from_opacity_effect = QGraphicsOpacityEffect()
        from_widget.setGraphicsEffect(from_opacity_effect)

        # to_widget에 QGraphicsOpacityEffect 추가
        to_opacity_effect = QGraphicsOpacityEffect()
        to_widget.setGraphicsEffect(to_opacity_effect)

        # from_widget 페이드 아웃 애니메이션
        fade_out = QPropertyAnimation(from_opacity_effect, b"opacity")
        fade_out.setDuration(500)  # 500ms
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        # to_widget 페이드 인 애니메이션
        fade_in = QPropertyAnimation(to_opacity_effect, b"opacity")
        fade_in.setDuration(500)  # 500ms
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)

        # 애니메이션 완료 시 visibility 설정
        def on_fade_out_finished():
            from_widget.setVisible(False)
            self.print("debug", f"{from_widget.objectName()} hidden after fade out.")

        def on_fade_in_finished():
            to_widget.setVisible(True)
            self.print("debug", f"{to_widget.objectName()} shown after fade in.")

        fade_out.finished.connect(on_fade_out_finished)
        fade_in.finished.connect(on_fade_in_finished)

        # 애니메이션 시작
        from_widget.setVisible(True)  # Ensure the from_widget is visible before fading out
        to_widget.setVisible(False)   # Ensure the to_widget is hidden before fading in
        fade_out.start()
        fade_in.start()

    def play_from_playlist(self):
        """ 플레이리스트에서 현재 동작 중인 위젯으로 재생 시작 """
        if not self.playlist:
            self.print("error", "Playlist is empty")
            return

        # 현재 트랙 재생
        current_file = self.playlist[self.playlist_track_index]
        self.print("info", f"Playing: {current_file}")
        self.fade_transition(self.player_widget_2, self.player_widget_1)

    def stop_all(self):
        """ 모든 위젯을 중지하고 로고를 표시합니다. """
        for widget in self.player_widgets:
            widget.setVisible(False)

        for player in self.players:
            player.stop()

        # 로고 위젯의 가시성을 직접 설정
        if hasattr(self, 'logo_widget') and self.logo_widget:
            self.logo_widget.setVisible(True)
            self.print("debug", "Logo widget set to visible.")

    def update_widget_sizes(self, event):
        """ MainWindow 크기 변경 시 위젯 크기를 업데이트합니다. """
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())

        # 로고 위치 조정 제거
        # set_logo_center(self)

    def resizeEvent(self, event):
        """ 메인 윈도우 크기 변경 시 로고 위젯 크기를 동적으로 조정합니다. """
        super().resizeEvent(event)


    def closeEvent(self, event):
        """ 창 닫기 이벤트 핸들러 창을 닫으면 전체 프로세스 종료 """
        self.print("info", "Closing player window, terminating process.")
        self.stdin_reader.stop()
        sys.exit(0)
            
    def set_logo_visibility(self, visible):
        """ 로고 위젯의 가시성을 설정합니다. """
        if hasattr(self, 'logo_widget') and self.logo_widget:
            self.logo_widget.setVisible(visible)
            self.print("debug", f"Logo visibility set to: {visible}")

if __name__ == "__main__":
    vp_pstatus_json = os.environ.get("VP_PSTATUS")
    app = QApplication(sys.argv)
    player = Player(pstatus=json.loads(vp_pstatus_json) if vp_pstatus_json else {})
    player.show()
    sys.exit(app.exec())