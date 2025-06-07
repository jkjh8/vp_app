import os, sys, json, vlc, win32process, win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from stdin import stdinReaderr
from background import set_background_color
from event_handler import handle_stdin_message
from logo_utils import set_logo_center, set_logo_size, update_logo_size, set_logo_file
from audio_utils import set_audio_device, get_audio_devices

class Player(QMainWindow):
    def __init__(self, pstatus=None):
        """Initialize the media player with the given status efficiently."""
        super().__init__()
        self.setWindowTitle("Media Player")
        self.setGeometry(100, 100, 800, 600)

        # Set process priority
        try:
            win32process.SetPriorityClass(win32process.GetCurrentProcess(), win32con.REALTIME_PRIORITY_CLASS)
            self.print("info", "Process priority set to REALTIME")
        except Exception as e:
            self.print("error", f"Failed to set process priority: {e}")

        # Initialize stdin reader for receiving commands
        self.stdin_reader = stdinReaderr()
        self.stdin_reader.message_received.connect(lambda: handle_stdin_message(self, self.stdin_reader.receive_udp_data))
        self.stdin_reader.start()

        # Set window icon
        icon_path = os.path.abspath("src/py/player/icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            self.print("info", f"Icon set from {icon_path}")
        else:
            self.print("error", f"Warning: Icon file not found at {icon_path}")

        # Logo utility bindings
        self.set_logo_file = lambda file: set_logo_file(self, file)
        self.set_logo_center = lambda: set_logo_center(self)
        self.set_logo_size = lambda size: set_logo_size(self, size)
        self.update_logo_size = lambda: update_logo_size(self)

        # Initialize variables from pstatus
        self.pstatus = pstatus or {}
        self.playlist_mode = bool(self.pstatus.get("playlistMode", False))
        self.playlist = []
        self.playlist_track_index = int(self.pstatus.get("playlistTrackIndex", 0))
        self.audio_devices = []
        self.image_time = int(self.pstatus.get("imageTime", 10))
        self.logo_file = self.pstatus.get("logo", {}).get("file", "")
        self.logo_show = bool(self.pstatus.get("logo", {}).get("show", True))
        self.logo_size = int(self.pstatus.get("logo", {}).get("size", 0))
        self.logo_width = 0
        self.logo_height = 0
        self.logo_svg = self.logo_file.lower().endswith(".svg")
        self.background_color = self.pstatus.get("background", "#000000")
        self.active_player_id = 0
        self.update_active_player_id(self.active_player_id)

        # Create widgets
        self.player_widgets = [QLabel(self) for _ in range(2)]
        self.logo_widget = QLabel(self)
        self.set_background_color = lambda color: set_background_color(self, color)
        self.set_background_color(self.background_color)
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())
            player.setVisible(False)

        # Initialize logo
        self.set_logo_file(self.logo_file)
        if not self.logo_file or not os.path.exists(self.logo_file):
            self.print("error", f"Logo file does not exist: {self.logo_file}")
        else:
            self.print("debug", f"Logo file exists: {self.logo_file}")
            self.print("debug", "Attempting to initialize SVG logo widget." if self.logo_svg else "Attempting to initialize Pixmap logo widget.")

        # Initialize VLC players and audio
        self.init_players()
        self.init_players_events()
        self.set_audio_device = lambda device_id: set_audio_device(self, device_id)
        self.get_audio_devices = lambda: get_audio_devices(self)
        get_audio_devices(self)
        set_audio_device(self, self.pstatus.get("device", {}).get("audiodevice", "default"))
        
    def set_fullscreen(self, value):
        """ Set the fullscreen mode for the player. """
        self.print("debug", f"Setting fullscreen mode to: {value}")
        if value:
            self.showFullScreen()
        else:
            self.showNormal()
        for player in self.players:
            player.set_fullscreen(value)
        self.print("set_fullscreen", { "value": value })
    
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

    def set_playlist_mode(self, value):
        """ Set the playlist mode (on/off). """
        self.print("debug", f"Setting playlist mode to: {value}")
        self.playlist_mode = value
        
    def update_active_player_id(self, idx):
        self.active_player_id = idx
        self.print("active_player_id", { "id": self.active_player_id })
        
    def play(self, idx=0):
        """ Play a specific player by index. """
        if idx < 0 or idx >= len(self.players):
            self.print("error", f"Invalid player index: {idx}")
            return
        
        # 해당 플레이어의 위젯이 숨김 상태면 활성화 하기
        if not self.player_widgets[idx].isVisible():
            # 트랜지션(페이드 효과)으로 위젯 전환
            self.fade_transition(idx)
            self.print("debug", f"Player widget {idx} shown with fade transition.")

        self.player[idx].play()
        
    def pause(self, idx=0):
        """ Pause a specific player by index. """
        if idx < 0 or idx >= len(self.players):
            self.print("error", f"Invalid player index: {idx}")
            return

        self.players[self.active_player_id].pause()
        
    def play_id(self, file):
        """Efficiently play a specific file by ID or path."""
        idx = self.active_player_id
        if not file:
            self.print("error", "No file provided to play.")
            return

        media_path = file.get("path", "")
        if not media_path:
            self.print("error", "Invalid media path provided.")
            return

        self.print("debug", f"Playing file: {media_path}")

        # Determine next available player index if current is busy
        if self.players[idx].is_playing() or (self.player_widgets[idx].isVisible() and self.player_widgets[idx].pixmap()):
            idx = 1 if idx == 0 else 0

        try:
            if file.get("is_image", True):
                self.display_image(file, idx)
            else:
                self.set_media(file, idx)
                self.players[idx].play()
            self.update_active_player_id(idx)
            self.fade_transition(idx)
        except Exception as e:
            self.print("error", f"Error playing file: {e}")
            
    def stop(self, idx=None):
        if idx is None:
            idx = self.active_player_id
        """ Stop a specific player by index. """
        self.players[idx].stop()
        self.stop_image(idx)  # Stop displaying any image
        self.player_widgets[idx].setVisible(False)  # Hide the player widget
        self.print("debug", f"Player {idx} stopped.")
    
    def set_media(self, file, idx=None):
        """ Set the media for a specific player. """
        if idx is None:
            idx = self.active_player_id

        if not file:
            self.print("error", "No file provided to set media.")
            return

        media_path = file.get("path", "")
        if not media_path:
            self.print("error", "Invalid media path provided.")
            return

        self.print("debug", f"Setting media for player {idx}: {media_path}")
        try:
            media = self.players[idx].get_instance().media_new(media_path)
            self.players[idx].set_media(media)
            self.players[idx].video_set_scale(0)  # Display media in its original size
            self.print('media_changed', { "idx": idx, "uuid": file.get("uuid", ""), "path": media_path })
            self.update_player_data(idx, None)  # Update player data after setting media
        except Exception as e:
            self.print("error", f"Error setting media: {e}")

    def on_end_reached(self, idx, event):
        """ Handle end reached event for a specific player. """
        self.print("info", f"Player {idx} has reached the end.")
        self.update_player_data(idx, event)
        self.print('end_reached', { "playlist_track_index": self.playlist_track_index, "active_player_id": self.active_player_id, "id": idx })

    def update_player_data(self, id, event):
        """ VLC 플레이어의 상태를 업데이트합니다. """
        try:
            state = str(self.players[id].get_state())  # State 객체를 문자열로 변환
            self.print("player_data", {
                "id": id,
                "event": str(event.type if event else "None"),  # 이벤트 타입을 문자열로 변환
                "media": self.players[id].get_media().get_mrl() if self.players[id].get_media() else "No media",
                "state": state,  # 문자열로 변환된 상태
                "time": self.players[id].get_time(),
                "duration": self.players[id].get_length(),
                "position": self.players[id].get_position(),
                "volume": self.players[id].audio_get_volume(),
                "rate": self.players[id].get_rate(),
                "is_playing": self.players[id].is_playing(),
                "fullscreen": self.players[id].get_fullscreen(),
            })
        except Exception as e:
            self.print("error", f"Error updating player data: {e}")
    
    def set_time(self, time, idx=None):
        """ Set the playback time for a specific player. """
        if idx is None:
            idx = self.active_player_id
        
        if not isinstance(time, int) or time < 0:
            self.print("error", "Invalid time value provided.")
            return

        try:
            self.players[idx].set_time(time)
            self.print("debug", f"Set player {idx} time to: {time}")
        except Exception as e:
            self.print("error", f"Error setting time for player {idx}: {e}")

    def print(self, type, data):
        """ Print the function name and data in a formatted way. """
        print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)


    def fade_transition(self, idx):
        """ 위젯 전환 """
        from_id = 1 if idx == 0 else 0  # 현재 동작 중인 위젯의 인덱스
        from_widget = self.player_widgets[from_id]  # 현재 동작 중인 위젯
        to_widget = self.player_widgets[idx]
        self.print("debug", f"Starting fade transition: from_widget={from_widget}, to_widget={to_widget}")
        to_widget.setVisible(True)  # Ensure the target widget is visible before fading in
        to_widget.raise_()  # Bring the target widget to the front

        from_widget.setVisible(False)
        if hasattr(from_widget, 'original_pixmap'):
            self.stop_image(from_id)  # Stop displaying image if it exists
        if self.players[from_id].is_playing():
            self.players[from_id].stop()

    def stop_all(self):
        """모든 플레이어와 위젯을 효율적으로 중지하고 로고를 표시합니다."""
        # 모든 플레이어 중지 및 위젯 숨김
        for idx, player in enumerate(self.players):
            if player.is_playing():
                player.stop()
            self.player_widgets[idx].clear()
            self.player_widgets[idx].setVisible(False)
            if hasattr(self.player_widgets[idx], 'original_pixmap'):
                del self.player_widgets[idx].original_pixmap

    def update_widget_sizes(self, event):
        """ MainWindow 크기 변경 시 위젯 크기를 업데이트합니다. 각위젯에 이미지가 있으면 함께 크기를 조정합니다. """
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())
            # 이미지 위젯이 있다면 크기를 조정합니다.
        self.update_image_size()
        
    def resizeEvent(self, event):
        """ 메인 윈도우 크기 변경 시 로고 위젯 크기를 동적으로 조정합니다. """
        super().resizeEvent(event)
        self.update_widget_sizes(event)
        self.update_image_size()
        self.set_logo_center()  # 로고 위치 조정

    def closeEvent(self, event):
        """ 창 닫기 이벤트 핸들러 창을 닫으면 전체 프로세스 종료 """
        self.print("info", "Closing player window, terminating process.")
        self.stdin_reader.stop()
        sys.exit(0)
            
    def display_image(self, file, idx=None):
        """Efficiently display an image on a specific player widget using PySide."""
        idx = self.active_player_id if idx is None else idx
        image_path = file.get("path")
        self.print("debug", f"Displaying image on player widget {idx}: {image_path}")

        try:
            # Stop any media currently playing on the player
            self.stop(idx)

            # Load and cache the pixmap only if the path changed
            widget = self.player_widgets[idx]
            if not hasattr(widget, 'original_pixmap') or not isinstance(widget.original_pixmap, QPixmap):
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    self.print("error", f"Failed to load image: {image_path}")
                    return
                widget.original_pixmap = pixmap
            else:
                pixmap = widget.original_pixmap

            self.print('media_changed', { "idx": idx, "uuid": file.get("uuid", ""), "path": image_path })

            # Scale the pixmap to fit the QLabel while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                widget.width(),
                widget.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            widget.setPixmap(scaled_pixmap)
            widget.setAlignment(Qt.AlignCenter)
            widget.setVisible(True)
            self.print("player_data", {
                "id": idx,
                "event": "display_image",
                "media": image_path,
                "state": "displaying_image",
                "time": 0,
                "duration": 0,
                "position": 0,
                "is_playing": 1,
            })
        except Exception as e:
            self.print("error", f"Error displaying image: {e}")
            
    def stop_image(self, idx=None):
        """Efficiently stop displaying the image on a specific player widget."""
        idx = self.active_player_id if idx is None else idx
        widget = self.player_widgets[idx]
        self.print("debug", f"Stopping image display on player widget {idx}")
        widget.clear()
        widget.setVisible(False)
        if hasattr(widget, 'original_pixmap'):
            del widget.original_pixmap
        self.print("player_data", {
            "id": idx,
            "event": "stop_image",
            "media": "",
            "state": "stopped_image",
            "time": 0,
            "duration": 0,
            "position": 0,
            "is_playing": 0,
        })
        
    def update_image_size(self):
        for idx, widget in enumerate(self.player_widgets):
            if hasattr(widget, 'original_pixmap') and widget.original_pixmap:
                pixmap = widget.original_pixmap
                scaled_pixmap = pixmap.scaled(
                    widget.width(),
                    widget.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                widget.setPixmap(scaled_pixmap)
                widget.setAlignment(Qt.AlignCenter)
            
if __name__ == "__main__":
    vp_pstatus_json = os.environ.get("VP_PSTATUS")
    app = QApplication(sys.argv)
    player = Player(pstatus=json.loads(vp_pstatus_json) if vp_pstatus_json else {})
    player.show()
    sys.exit(app.exec())