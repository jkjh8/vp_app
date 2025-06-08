import os, sys, json, vlc, win32process, win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from stdin import stdinReaderr
from ui_utils import set_background_color, set_fullscreen, fade_transition
from event_handler import handle_stdin_message
from logo_utils import set_logo_center, set_logo_size, update_logo_size, set_logo_file
from audio_utils import set_audio_device, get_audio_devices
from player_utils import init_players, init_players_events, update_active_player_id, update_player_data, stop, set_time

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

        # Initialize variables from pstatus
        self.pstatus = pstatus or {}
        self.playlist_mode = bool(self.pstatus.get("playlistMode", False))
        self.tracks = []
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
        self.fullscreen = bool(self.pstatus.get("fullscreen", False))
        self.active_player_id = 0
        
        self.instances = []
        self.players = []
        self.current_files = [{}, {}]
        
        # Create widgets
        self.player_widgets = [QLabel(self) for _ in range(2)]
        self.logo_widget = QLabel(self)
        self.set_background_color = lambda color: set_background_color(self, color)
        self.set_background_color(self.background_color)
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())
            player.setVisible(False)

        # Initialize logo
        self.set_logo_file = lambda file: set_logo_file(self, file)
        self.set_logo_center = lambda: set_logo_center(self)
        self.set_logo_size = lambda size: set_logo_size(self, size)
        self.update_logo_size = lambda: update_logo_size(self)
        self.set_logo_visible = lambda visible: setattr(self.logo_widget, 'setVisible', visible)
        
        self.set_logo_file(self.logo_file)
        if not self.logo_file or not os.path.exists(self.logo_file):
            self.print("error", f"Logo file does not exist: {self.logo_file}")
        else:
            self.print("debug", f"Logo file exists: {self.logo_file}")
            self.print("debug", "Attempting to initialize SVG logo widget." if self.logo_svg else "Attempting to initialize Pixmap logo widget.")

        # Initialize VLC players and audio
        self.init_players = lambda: init_players(self)
        self.init_players_events = lambda: init_players_events(self)
        self.update_active_player_id = lambda idx: update_active_player_id(self, idx)
        self.update_player_data = lambda id, event: update_player_data(self, id, event)
        self.stop = lambda idx=None: stop(self, idx)
        self.set_time = lambda time, idx=None: set_time(self, time, idx)
        
        self.update_active_player_id(self.active_player_id)
        
        self.init_players()
        self.init_players_events()
        
        # audio device management
        self.set_audio_device = lambda device_id: set_audio_device(self, device_id)
        self.get_audio_devices = lambda: get_audio_devices(self)
        get_audio_devices(self)
        set_audio_device(self, self.pstatus.get("device", {}).get("audiodevice", "default"))
        
        # fullscreen mode
        self.set_fullscreen = lambda value: set_fullscreen(self, value)
        self.set_fullscreen(self.fullscreen)
        
        # fade transition
        self.fade_transition = lambda idx: fade_transition(self, idx)
        
    def print(self, type, data):
        """함수명과 데이터를 효율적으로 포맷하여 출력합니다."""
        print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)

    def set_playlist_mode(self, value):
        """ Set the playlist mode (on/off). """
        self.print("debug", f"Setting playlist mode to: {value}")
        self.playlist_mode = value

    def play(self, idx=0):
        """ Play a specific player by index. """
        if self.active_player_id != idx:
            self.update_active_player_id(idx)
            self.print("debug", f"Active player ID updated to: {idx}")

        if self.current_files[idx].get("is_image", True):
            # 이미지 재생
            self.display_image(self.current_files[idx], idx)
            self.print("debug", f"Image displayed on player widget {idx}.")
            return
        else:
            # 미디어 재생
            self.players[idx].play()

        # 해당 플레이어의 위젯이 숨김 상태면 활성화 하기
        if not self.player_widgets[idx].isVisible():
            # 트랜지션(페이드 효과)으로 위젯 전환
            self.fade_transition(idx)
            self.print("debug", f"Player widget {idx} shown with fade transition.")


    def pause(self, idx=0):
        """ Pause a specific player by index. """
        if idx < 0 or idx >= len(self.players):
            self.print("error", f"Invalid player index: {idx}")
            return

        self.players[self.active_player_id].pause()
        
    def play_id(self, file):
        """Efficiently play a specific file by ID or path."""
        idx = self.active_player_id

        # Determine next available player index if current is busy
        if self.players[idx].is_playing() or (self.player_widgets[idx].isVisible() and self.player_widgets[idx].pixmap()):
            idx = 1 if idx == 0 else 0
            
        # set Media file for the player
        self.set_media(file, idx)
        # Update the current file for the player
        self.current_files[idx] = file

        try:
            if file.get("is_image") == False:
                self.players[idx].play()
            self.update_active_player_id(idx)
            self.fade_transition(idx)
        except Exception as e:
            self.print("error", f"Error playing file: {e}")
            
    def playlist_play(self, idx=None):
        """ Play the current track in the playlist. """
        if idx is not None:
            if idx < 0 or idx >= len(self.tracks):
                self.print("error", f"Invalid playlist index: {idx}")
                return
            self.playlist_track_index = idx
        if not self.tracks or self.playlist_track_index >= len(self.tracks):
            self.print("error", "Playlist is empty or index out of range.")
            return

        file = self.tracks[self.playlist_track_index]
        self.print("debug", f"Playing track {self.playlist_track_index}: {file.get('path', 'Unknown')}")
        self.play_id(file)
        # set next track load next player
        self.print("debug", f"Setting next track index to: {self.playlist_track_index + 1}")
        
    
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

        self.print("debug", f"Setting media for player {idx}: {media_path}")

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
            
    def set_tracks(self, tracks):
        """ Set the playlist tracks efficiently. """
        if not isinstance(tracks, list):
            self.print("error", "Invalid tracks format, expected a list.")
            return

        self.tracks = tracks
        self.print("debug", f"Playlist set with {len(tracks)} tracks.")

    def on_end_reached(self, idx, event):
        """ Handle end reached event for a specific player. """
        self.print("info", f"Player {idx} has reached the end.")
        self.update_player_data(idx, event)
        self.print('end_reached', { "playlist_track_index": self.playlist_track_index, "active_player_id": self.active_player_id, "id": idx })


    





    
    def stop_all(self):
        """모든 플레이어와 위젯을 효율적으로 중지하고 로고를 표시합니다."""
        # 모든 플레이어 중지 및 위젯 숨김
        for idx in range(len(self.player_widgets)):
            self.stop(idx)

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