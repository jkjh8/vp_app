import os, sys, json, vlc, win32process, win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from stdin import stdinReaderr
from ui_utils import set_background_color, set_fullscreen, fade_transition
from event_handler import handle_stdin_message
from logo_utils import set_logo_center, set_logo_size, update_logo_size, set_logo_file, set_logo_visibility
from audio_utils import set_audio_device, get_audio_devices, set_audio_device_with_retry
from player_utils import init_players, init_players_events, update_active_player_id, update_player_data, stop, pause, stop_all, set_media, play_id, play, on_end_reached
from image_util import display_image, update_image_size, stop_image, set_image_time, update_widget_sizes
from playlist_utils import set_playlist_mode, set_time, set_tracks, update_track_index, playlist_play, next_file_load, next, previous, image_timer

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
        self.audio_devices = []
        
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
            
        self.update_widget_sizes = lambda event: update_widget_sizes(self, event)

        # Initialize logo
        self.set_logo_file = lambda file: set_logo_file(self, file)
        self.set_logo_center = lambda: set_logo_center(self)
        self.set_logo_size = lambda size: set_logo_size(self, size)
        self.update_logo_size = lambda: update_logo_size(self)
        self.set_logo_visibility = lambda show: set_logo_visibility(self, show)

        self.set_logo_file(self.logo_file)
        if not self.logo_file or not os.path.exists(self.logo_file):
            self.print("error", f"Logo file does not exist or is invalid: {self.logo_file}")
            return
        
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
        self.play_id = lambda file: play_id(self, file)
        self.play = lambda idx=0: play(self, idx)
        self.on_end_reached = lambda idx, event: on_end_reached(self, idx, event)
        self.pause = lambda idx=0: pause(self, idx)
        self.stop = lambda idx=None: stop(self, idx)
        self.stop_all = lambda: stop_all(self)
        
        self.update_active_player_id(self.active_player_id)
        
        self.init_players()
        self.init_players_events()
        
        # playlist mode
        self.set_playlist_mode = lambda value: set_playlist_mode(self, value)
        self.set_time = lambda time, idx=None: set_time(self, time, idx)
        self.update_track_index = lambda idx: update_track_index(self, idx)
        self.set_tracks = lambda tracks: set_tracks(self, tracks)
        self.playlist_play = lambda idx=0: playlist_play(self, idx)
        self.next = lambda: next(self)
        self.previous = lambda: previous(self)
        self.next_file_load = lambda idx=None: next_file_load(self, idx)
        self.image_timer = lambda: image_timer(self)
        
        # fullscreen mode
        self.set_fullscreen = lambda value: set_fullscreen(self, value)
        self.set_fullscreen(self.fullscreen)
        
        # fade transition
        self.fade_transition = lambda idx: fade_transition(self, idx)
        
        # audio device management
        self.set_audio_device_with_retry = lambda device_id: set_audio_device_with_retry(self, device_id)
        self.set_audio_device = lambda device_id: set_audio_device(self, device_id)
        self.get_audio_devices = lambda: get_audio_devices(self)
        get_audio_devices(self)
        # set audio device 확인 필요
        self.set_audio_device_result = False
        set_audio_device_with_retry(self, self.pstatus.get("device", {}).get("audiodevice", "default"))
        
        self.image_timer_instance = QTimer(self)  # QTimer 객체 생성
        self.image_timer_instance.timeout.connect(lambda: self.on_end_reached(self.active_player_id, None))
        
    def print(self, type, data):
        """함수명과 데이터를 효율적으로 포맷하여 출력합니다."""
        print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)
        
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