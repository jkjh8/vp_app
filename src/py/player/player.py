import os, sys, json, vlc, win32process, win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from stdin import stdinReaderr
from ui_utils import set_background_color, set_fullscreen, fade_transition
from event_handler import handle_stdin_message
from logo_utils import set_logo_center, set_logo_size, update_logo_size, set_logo_file
from audio_utils import set_audio_device, get_audio_devices
from player_utils import init_players, init_players_events, update_active_player_id, update_player_data, stop, set_time, pause, stop_all, set_media
from image_util import display_image, update_image_size, stop_image, set_image_time

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
        self.track_index = int(self.pstatus.get("playlistTrackIndex", 0))
        self.next_track_index = 0
        self.active_player_id = 0 
        self.next_player_index = 1 if self.active_player_id == 0 else 0
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
            self.print("error", f"Logo file does not exist or is invalid: {self.logo_file}")
            return

        # Initialize logo widget based on file type
        try:
            if self.logo_svg:
                self.logo_widget = QSvgWidget(self.logo_file, self)
                self.logo_widget.setGeometry(0, 0, self.logo_width, self.logo_height)
                self.print("debug", "SVG logo widget initialized successfully.")
            else:
                pixmap = QPixmap(self.logo_file)
                if pixmap.isNull():
                    self.print("error", "Failed to load image: Pixmap is null.")
                    return
                self.logo_widget.setPixmap(pixmap.scaled(self.logo_width, self.logo_height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.print("debug", "Pixmap logo widget initialized successfully.")
        except Exception as e:
            self.print("error", f"Error initializing logo widget: {e}")
        
        # Initialize image utilities
        self.display_image = lambda file, idx: display_image(self, file, idx)
        self.update_image_size = lambda: update_image_size(self)
        self.stop_image = lambda idx=None: stop_image(self, idx)
        self.set_image_time = lambda time: set_image_time(self, time)

        # Initialize VLC players and audio
        self.init_players = lambda: init_players(self)
        self.init_players_events = lambda: init_players_events(self)
        self.update_active_player_id = lambda idx: update_active_player_id(self, idx)
        self.update_player_data = lambda id, event: update_player_data(self, id, event)
        self.set_media = lambda file, idx=None: set_media(self, file, idx)
        self.pause = lambda idx=0: pause(self, idx)
        self.stop = lambda idx=None: stop(self, idx)
        self.stop_all = lambda: stop_all(self)
        self.set_time = lambda time, idx=None: set_time(self, time, idx)
        
        self.update_active_player_id(self.active_player_id)
        
        self.init_players()
        self.init_players_events()
        
        
        # fullscreen mode
        self.set_fullscreen = lambda value: set_fullscreen(self, value)
        self.set_fullscreen(self.fullscreen)
        
        # fade transition
        self.fade_transition = lambda idx: fade_transition(self, idx)
        
        # audio device management
        self.set_audio_device = lambda device_id: set_audio_device(self, device_id)
        self.get_audio_devices = lambda: get_audio_devices(self)
        get_audio_devices(self)
        # set audio device 확인 필요
        set_audio_device(self, self.pstatus.get("device", {}).get("audiodevice", "default"))
        
        self.image_timer_instance = QTimer(self)  # QTimer 객체 생성
        self.image_timer_instance.timeout.connect(lambda: self.on_end_reached(self.active_player_id, None))
        
    def print(self, type, data):
        """함수명과 데이터를 효율적으로 포맷하여 출력합니다."""
        print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)
        
    def update_track_index(self, idx):
        """ Update the current track index. """
        if idx < 0 or idx >= len(self.tracks):
            self.print("error", f"Invalid track index: {idx}")
            return
        self.track_index = idx
        self.print("track_index", { "index": self.track_index })

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

    def play_id(self, file):
        """Efficiently play a specific file by ID or path."""
        idx = self.active_player_id

        # Determine next available player index if current is busy
        if self.players[idx].is_playing() or (self.player_widgets[idx].isVisible() and self.player_widgets[idx].pixmap()):
            idx = 1 if idx == 0 else 0
            
        # set Media file for the player
        self.set_media(file, idx)

        try:
            if file.get("is_image") == False:
                self.players[idx].play()
            self.update_active_player_id(idx)
            self.fade_transition(idx)
        except Exception as e:
            self.print("error", f"Error playing file: {e}")
            
    def playlist_play(self, idx = 0):
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
        if self.current_files[self.active_player_id].get("is_image", False):
            # If the current file is an image, start the image timer
            self.image_timer()
        # self.image_timer()

    def next(self):
        if not self.playlist_mode:
            self.print("error", "Next track can only be used in playlist mode.")
            return

        if self.image_timer_instance.isActive():
            self.image_timer_instance.stop()
            self.print("debug", "Existing image timer stopped.")

        if self.current_files[self.next_player_index].get("is_image", False):
            self.track_index = self.next_track_index  # Update track_index for image playback
            self.update_track_index(self.track_index)
        else:
            self.players[self.next_player_index].play()
            self.track_index = self.next_track_index  # Update track_index when playback starts
            self.update_track_index(self.track_index)

        self.fade_transition(self.next_player_index)
        self.next_file_load()
        self.image_timer()


    def next_file_load(self, idx=None):
        """ Load the next file in the playlist. """
        self.print("debug", f"Current track index: {self.track_index}, Next track index: {self.next_track_index}")

        if idx is not None:
            self.next_track_index = idx
        else:
            self.next_track_index = self.track_index + 1

        if self.next_track_index >= len(self.tracks):
            self.next_track_index = 0

        self.next_player_index = 1 if self.active_player_id == 0 else 0
        self.set_media(self.tracks[self.next_track_index], self.next_player_index)
        self.print("debug", f"Updated next track index to: {self.next_track_index}")

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

        # 새로운 타이머 시작
        self.image_timer_instance.timeout.connect(lambda: self.on_end_reached(self.active_player_id, None))
        self.image_timer_instance.start(self.image_time * 1000)
        self.print("debug", f"Image timer started for {self.image_time} seconds.")

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

        # 디버깅 로그 추가
        self.print("debug", f"Event data received: {event}")

        try:
            self.update_player_data(idx, event)
            self.print('end_reached', {
                "playlist_track_index": self.track_index,
                "active_player_id": self.active_player_id,
            })
        except Exception as e:
            self.print("error", f"Error handling end reached event: {e}")

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
            
    
            
if __name__ == "__main__":
    vp_pstatus_json = os.environ.get("VP_PSTATUS")
    app = QApplication(sys.argv)
    player = Player(pstatus=json.loads(vp_pstatus_json) if vp_pstatus_json else {})
    player.show()
    sys.exit(app.exec())