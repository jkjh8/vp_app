import os, io, sys, json, time, threading, vlc, win32process, win32con
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtSvg import QSvgRenderer

# 표준 입출력 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

class stdinRead(QThread):
    message_received = Signal(str)
    def __init__(self):
        super().__init__()
        self.running = True
        self.receive_udp_data = ""

    def run(self):
        while self.running:
            try:
                if self.running == False:
                    break
                data = sys.stdin.readline()
                if data:
                    self.receive_udp_data = data.strip()
                    self.message_received.emit(self.receive_udp_data)
            except Exception as e:
                self.print_json("error", {"message": f"Error reading stdin: {e}"})
                break

    def stop(self):
        self.running = False

class Player(QMainWindow):
    def __init__(self, pstatus=None, app_path=None):
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
        self.stdin_reader = stdinRead()
        self.stdin_reader.message_received.connect(self.handle_stdin_message)
        self.stdin_reader.start()

        # Set window icon
        icon_path = os.path.join(app_path, "src/icon.png")
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
        self.set_background_color(self.background_color)
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())
            player.setVisible(False)

        self.set_logo_file(self.logo_file)
        if not self.logo_file or not os.path.exists(self.logo_file):
            self.print("error", f"Logo file does not exist or is invalid: {self.logo_file}")
            return


        self.update_active_player_id(self.active_player_id)
        
        self.init_players()
        self.init_players_events()
        
        
        # fullscreen mode
        self.set_fullscreen(self.fullscreen)

        # audio device management
        self.get_audio_devices()
        # set audio device 확인 필요
        self.set_audio_device_result = False
        self.set_audio_device_with_retry(self.pstatus.get("device", {}).get("audiodevice", "default"))
        
        self.image_timer_instance = QTimer(self)  # QTimer 객체 생성
        self.image_timer_instance.timeout.connect(lambda: self.on_end_reached(self.active_player_id, None))
        
    # 명령 처리 함수
    def handle_stdin_message(self, data):
        """ Handle commands received from stdin. """
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            self.print("error", "Invalid JSON received from stdin")
            return
        command = data.get("command")
        if not isinstance(command, str):
            self.print("error", f"Invalid command type: {type(command)}. Expected a string.")
            return
        # 짧은 시간 내 중복 메시지 필터링
        current_time = time.time()
        if not hasattr(self, 'last_command_time'):
            self.last_command_time = {}
        last_time = self.last_command_time.get(command, 0)
        if current_time - last_time < 0.1:  # 0.5초 이내 중복 메시지 무시
            self.print("debug", f"Skipping duplicate command within short interval: {command}")
            return
        self.last_command_time[command] = current_time
        # 명령어에 따라 적절한 함수 호출
        dispatch = {
            # logo
            "show_logo": lambda data: self.set_logo_visibility(data.get("show", True)),
            "logo_file": lambda data: self.set_logo_file(data.get("file", "")),
            "logo_size": lambda data: self.set_logo_size(int(data.get("size", 0))),
            # player
            "set_media": lambda data: self.set_media(data.get("file", {}), int(data.get("idx", 0))),
            "playid": lambda data: self.play_id(data.get("file", {})),
            "play": lambda data: self.play(int(data.get("idx", 0))),
            "pause": lambda data: self.pause(int(data.get("idx", 0))),
            "stop": lambda data: self.stop(int(data.get("idx", 0))),
            "stop_all": lambda data: self.stop_all(),
            # audio devices
            "set_audio_device": lambda data: self.set_audio_device(data.get("device_id", "")),
            "get_audio_devices": lambda data: self.get_audio_devices(),
            # playlist
            "playlist_mode": lambda data: self.set_playlist_mode(bool(data.get("value", False))),
            "playlist_play": lambda data: self.playlist_play(int(data.get("idx", 0))),
            "set_tracks": lambda data: self.set_tracks(data.get("tracks", [])),
            "image_time": lambda data: self.set_image_time(int(data.get("time", 0))),
            "set_track_index": lambda data: self.update_track_index(int(data.get("index", 0))),
            "next": lambda data: self.next(),
            "previous": lambda data: self.previous(),
            "set_time": lambda data: self.set_time(int(data.get("time", 0)), int(data.get("idx", 0))),
            # etc
            "set_fullscreen": lambda data: self.set_fullscreen(data.get("value", False)),
            "background_color": lambda data: self.set_background_color(data.get("color", "#000000")),
        }
        func = dispatch.get(command)
        if func:
            try:
                if command == "set_track_index":
                    pass
                func(data)
            except Exception as e:
                self.print("error", f"Error executing command '{command}': {e}")
        else:
            self.print("error", f"Unknown command: {command}")
            
        
    def print(self, type, data):
        """함수명과 데이터를 효율적으로 포맷하여 출력합니다."""
        print(json.dumps({"type": type, "data": data}, ensure_ascii=False, separators=(",", ":")), flush=True)
        
    def resizeEvent(self, event):
        """ 메인 윈도우 크기 변경 시 로고 위젯 크기를 동적으로 조정합니다. """
        super().resizeEvent(event)
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())
        self.update_image_size()
        self.set_logo_center()  # 로고 위치 조정

    def closeEvent(self, event):
        """ 창 닫기 이벤트 핸들러 창을 닫으면 전체 프로세스 종료 """
        self.print("info", "Closing player window, terminating process.")
        self.stdin_reader.stop()
        sys.exit(0)
        
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
                
    # 로고 함수들
    def set_logo_center(self):
        """ 로고 위젯을 중앙에 위치시키고 크기를 조정합니다. """
        if not hasattr(self, 'logo_widget') or not self.logo_widget:
            self.print("error", "Logo widget is not initialized.")
            return
        logo_x = (self.width() - self.logo_width) // 2
        logo_y = (self.height() - self.logo_height) // 2
        self.logo_widget.setGeometry(logo_x, logo_y, self.logo_width, self.logo_height)
        self.logo_widget.setVisible(self.logo_show)
        
    def set_logo_size(self, size):
        """ 로고 크기를 조정합니다. """
        try:
            self.logo_size = size
            self.update_logo_size()  # 새로운 크기 계산

            if not self.logo_svg and self.logo_widget and isinstance(self.logo_widget, QLabel):
                # Pixmap 로고의 경우 크기 조정된 Pixmap을 다시 설정
                pixmap = QPixmap(self.logo_file)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.logo_width,
                        self.logo_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.logo_widget.setPixmap(scaled_pixmap)

            self.set_logo_center()  # 크기와 위치 업데이트
        except Exception as e:
            self.print("error", f"Error setting logo size: {e}")
                
    def update_logo_size(self):
        """ 로고 파일의 원본 크기를 확인하고 self.logo_width와 self.logo_height를 업데이트합니다. """
        if not self.logo_file or not os.path.exists(self.logo_file):
            self.print("error", "Logo file does not exist or path is empty.")
            return

        if self.logo_svg:
            # SVG 파일의 경우 QSvgRenderer를 사용하여 원본 크기를 가져옴
            try:
                svg_renderer = QSvgRenderer(self.logo_file)
                if not svg_renderer.isValid():
                    self.print("error", "Failed to load SVG logo file.")
                    return

                original_width = svg_renderer.defaultSize().width()
                original_height = svg_renderer.defaultSize().height()

                if self.logo_size > 0:
                    self.logo_width = self.logo_size
                    self.logo_height = int(original_height * (self.logo_size / original_width))
                else:
                    self.logo_width = original_width
                    self.logo_height = original_height
            except Exception as e:
                self.print("error", f"Error loading SVG logo: {e}")
        else:
            # Pixmap 파일의 경우 원본 크기를 확인
            pixmap = QPixmap(self.logo_file)
            if pixmap.isNull():
                self.print("error", "Failed to load Pixmap logo file.")
                return

            original_width = pixmap.width()
            original_height = pixmap.height()

            if self.logo_size > 0:
                self.logo_width = self.logo_size
                self.logo_height = int(original_height * (self.logo_size / original_width))
            else:
                self.logo_width = original_width
                self.logo_height = original_height

        self.print("debug", f"Logo size updated: width={self.logo_width}, height={self.logo_height}")
        
    def set_logo_file(self, file):
        """ 로고 파일 경로를 설정하고 기존 로고를 제거한 뒤 새로운 로고 위젯을 초기화합니다. """
        if not file or not os.path.exists(file):
            self.print("error", f"Invalid logo file path: {file}")
            return

        # 기존 로고 위젯 제거
        if hasattr(self, 'logo_widget') and self.logo_widget:
            self.logo_widget.setVisible(False)  # 기존 로고 숨기기
            self.logo_widget.deleteLater()  # 기존 로고 위젯 삭제
            self.logo_widget = None

        # 로고 파일 경로 및 관련 속성 업데이트
        self.logo_file = file
        self.logo_svg = self.logo_file.lower().endswith(".svg")
        self.print("debug", f"Logo file set to: {self.logo_file}")

        # 로고 크기 업데이트
        self.update_logo_size()

        # 로고 위젯 초기화
        if self.logo_svg:
            try:
                self.logo_widget = QSvgWidget(self.logo_file, self)
            except Exception as e:
                self.print("error", f"Failed to initialize SVG logo widget: {e}")
                return
        else:
            try:
                pixmap = QPixmap(self.logo_file)
                if not pixmap.isNull():
                    self.logo_widget = QLabel(self)  # 새로운 QLabel 생성
                    self.logo_widget.setPixmap(
                        pixmap.scaled(
                            self.logo_width,
                            self.logo_height,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                    )
                else:
                    self.print("error", "Pixmap is null. Failed to load image.")
                    return
            except Exception as e:
                self.print("error", f"Failed to initialize Pixmap logo widget: {e}")
                return

        # 로고 위젯의 크기와 위치를 중앙으로 설정
        self.set_logo_center()
        
    def set_logo_visibility(self, visible):
        """ 로고 위젯의 가시성을 설정합니다. """
        if hasattr(self, 'logo_widget') and self.logo_widget:
            self.logo_widget.setVisible(visible)
            self.print("debug", f"Logo visibility set to: {visible}")
            
    def display_image(self, file, idx=None):
        """Efficiently display an image on a specific player widget using PySide."""
        idx = self.active_player_id if idx is None else idx
        image_path = file.get("path")

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
        if self.image_timer_instance.isActive():
            self.image_timer_instance.stop()
        idx = self.active_player_id if idx is None else idx
        widget = self.player_widgets[idx]
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
        
    def set_image_time(self, time):
        self.image_time = time
        self.print("set_image_time", {"value" : self.image_time})

    def update_widget_sizes(self, event):
        """ MainWindow 크기 변경 시 위젯 크기를 업데이트합니다. 각위젯에 이미지가 있으면 함께 크기를 조정합니다. """
        for player in self.player_widgets:
            player.setGeometry(0, 0, self.width(), self.height())
            # 이미지 위젯이 있다면 크기를 조정합니다.
        self.update_image_size()
        
    def set_background_color(self, color):
        """ 배경 색상을 설정하는 함수 """
        self.background_color = color
        self.setStyleSheet(f"background-color: {self.background_color};")  # 메인 윈도우 배경색 변경
        for widget in self.player_widgets:
            widget.setStyleSheet(f"background-color: {self.background_color};")

    def set_fullscreen(self, value):
        """ Set the fullscreen mode for the player. """
        if value:
            self.showFullScreen()
        else:
            self.showNormal()
        for player in self.players:
            player.set_fullscreen(value)
        self.print("set_fullscreen", { "value": value })
        
    def fade_transition(self, idx):
        """ 위젯 전환 """
        from_id = 1 if idx == 0 else 0  # 현재 동작 중인 위젯의 인덱스
        from_widget = self.player_widgets[from_id]  # 현재 동작 중인 위젯
        to_widget = self.player_widgets[idx]
        to_widget.setVisible(True)  # Ensure the target widget is visible before fading in
        to_widget.raise_()  # Bring the target widget to the front
        self.update_active_player_id(idx)  # Update the active player ID
        
        
        from_widget.setVisible(False)
        if hasattr(from_widget, 'original_pixmap'):
            self.stop_image(from_id)  # Stop displaying image if it exists
        if self.players[from_id].is_playing():
            self.players[from_id].stop()
            
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

    def init_players(self):
        self.print("info", f"Initializing VLC players...")
        # 공통 옵션을 변수로 선언
        vlc_args = [
            "--no-video-title-show",
            "--avcodec-hw=any",
            "--no-drop-late-frames",
            "--no-skip-frames"
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
            def make_handler(func, *args):
                """Create a handler function that calls func with args."""
                def handler(event):
                    try:
                        func(*args, event)
                    except Exception as e:
                        print(f"Error in handler: {e}")
                return handler
            
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
        """ Move to the previous track. """
        if not self.playlist_mode:
            self.print("error", "Previous track can only be used in playlist mode.")
            return

        if self.players[self.active_player_id].get_time() > 5000:
            self.players[self.active_player_id].set_time(0)
            return

        if self.image_timer_instance.isActive():
            self.image_timer_instance.stop()
            self.print("debug", "Existing image timer stopped.")

        # Calculate previous track index
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

    def set_time(self, time, idx=None):
        """Efficiently set the playback time for a specific player."""
        idx = self.active_player_id if idx is None else idx

        if not isinstance(time, int) or time < 0:
            self.print("error", "Invalid time value provided.")
            return

        try:
            self.players[idx].set_time(time)
        except Exception as e:
            self.print("error", f"Error setting time for player {idx}: {e}")

    def image_timer(self):
        """Efficiently set a timer for image playback in playlist mode."""
        timer = self.image_timer_instance

        if timer.isActive():
            timer.stop()
            try:
                timer.timeout.disconnect()
                self.print("debug", "Existing image timer stopped and disconnected.")
            except RuntimeError:
                self.print("debug", "Timeout signal not connected, skipping disconnect.")

        if not self.playlist_mode:
            self.print("error", "Image timer can only be set in playlist mode.")
            return

        if not self.tracks or self.track_index >= len(self.tracks):
            self.print("debug", "Playlist is empty or index is out of range.")
            return

        current_file = self.current_files[self.active_player_id]
        if not current_file.get("is_image", False):
            self.print("debug", "Current file is not an image, skipping image timer setup.")
            return

        show_time = current_file.get("time", self.image_time)
        timer.start(show_time * 1000)
        self.print("debug", f"Image timer started for {show_time} seconds.")

if __name__ == "__main__":
    vp_pstatus_json = os.environ.get("VP_PSTATUS")
    app_path = os.environ.get("APP_PATH", "")
    app = QApplication(sys.argv)
    player = Player(pstatus=json.loads(vp_pstatus_json) if vp_pstatus_json else {}, app_path=app_path)
    player.show()
    sys.exit(app.exec())