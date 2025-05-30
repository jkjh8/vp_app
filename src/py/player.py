import os
import sys
import socket
import threading
import win32process, win32con
import json
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget

import vlc

class stdinReaderr(QThread):
    message_received = Signal(str)
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                if self.running == False:
                    break
                data = sys.stdin.readline()
                if data:
                    self.message_received.emit(data.strip())
            except Exception as e:
                self.print_json("error", {"message": f"Error reading stdin: {e}"})
                break

    def stop(self):
        self.running = False

class Player(QMainWindow):
    def __init__(self, pstatus=None):
        super().__init__()
        self.pstatus = pstatus if pstatus else {}

        self.setWindowTitle("VP")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))
        # logo_label과 svg_widget 초기화
        self.logo_label = QLabel(self)
        self.logo_label.setVisible(False)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.svg_widget = QSvgWidget(self)
        self.svg_widget.setVisible(False)
        # 이미지 표시를 위한 레이블 추가
        self.image_label = QLabel(self)
        self.image_label.setVisible(False)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        # 레이아웃 설정
        layout = QVBoxLayout()
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.initPlayer()
        self.initStdinThread()
        self.initUi()
        try:
            handle = win32process.GetCurrentProcess()
            win32process.SetPriorityClass(handle, win32con.REALTIME_PRIORITY_CLASS)
        except Exception as e:
            self.print_json("error", {"message": f"우선순위 설정 실패: {e}"})

    def initUi(self):
        self.set_background_color(self.pstatus.get("background", "white"))
        self.set_fullscreen(self.pstatus.get("fullscreen", False))
        self.set_logo(self.pstatus.get("logo", {}).get("path", ""))
        self.show_logo(self.pstatus.get("logo", {}).get("show", False))

    def initStdinThread(self):
        # Initialize stdin thread
        self.stdin_thread = stdinReaderr()
        self.stdin_thread.message_received.connect(self.handle_message)
        self.stdin_thread.start()

    def initPlayer(self):
        # Initialize VLC player with hardware decoding options
        self.instance = vlc.Instance(
            "--no-video-title-show",
            "--avcodec-hw=any",
            "--no-drop-late-frames",
            "--no-skip-frames"
        )
        self.player = self.instance.media_player_new()
        
        # 플레이어 캔버스 지정하기
        self.player.set_hwnd(int(self.winId()))
        # 이벤트 핸들러 등록하기
        self.init_events()
        
    def init_events(self):
        # 이벤트 등록하기
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerBuffering, self.on_buffering)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerTimeChanged, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerPlaying, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerPaused, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerStopped, self.update_player_data)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEncounteredError, self.on_error)
        self.player.event_manager().event_attach(vlc.EventType.MediaPlayerMediaChanged, self.update_player_data)
        
    def on_buffering(self, event):
        buffering = getattr(event.u, "buffering", None)
        if buffering is not None:
            self.pstatus['player']['buffering'] = buffering
        else:
            self.print_json("error", {"message": "Buffering event received, but no buffering info found."})

    def on_end_reached(self, event):
        self.update_player_data(event)
        # self.player.stop()

    def on_error(self, event):
        self.print_json("error", {"message": "Error occurred"})

    def update_player_data(self, event=None):
        event_type = getattr(event, "type", "manual")
        self.pstatus['player']['event'] = str(event_type)
        media = self.player.get_media()
        if media is not None:
            self.pstatus['player']['filename'] = media.get_mrl()
        else:
            self.pstatus['player']['filename'] = ""
        self.pstatus['player']['duration'] = self.player.get_length()
        self.pstatus['player']['time'] = self.player.get_time()
        self.pstatus['player']['position'] = self.player.get_position()
        self.pstatus['player']['playing'] = self.player.is_playing()
        self.pstatus['player']['volume'] = self.player.audio_get_volume()
        self.pstatus['player']['speed'] = self.player.get_rate()
        self.pstatus['player']['fullscreen'] = self.player.get_fullscreen()
        self.print_json("info", self.pstatus)

    @Slot(str)
    def handle_message(self, data):
        # stdin에서 읽은 데이터는 이미 str이므로 decode 필요 없음
        self.receive_udp_data = data.strip()
        # JSON 데이터 처리
        data = json.loads(self.receive_udp_data)
        if not isinstance(data, dict):
            self.print_json("error", {"message": "Invalid data format. Expected a JSON object."})
            return
        if "command" not in data:
            self.print_json("error", {"message": "Missing 'command' in data."})
            return
        command = data["command"]
        if command == 'set':
            file = data.get("file", {})
            self.currentFile = data.get("file", {})
            if not self.currentFile:
                self.print_json("error", {"message": "No file data provided."})
                return
            if not self.currentFile.get("is_image", True):
                media_path = self.currentFile.get("path", "")
                if not media_path:
                    self.print_json("error", {"message": "No media path provided."})
                    return
                self.set_media(media_path.strip())
        elif command == 'playid':
            self.pstatus['current'] = data.get("file", {})
            if not self.pstatus['current']:
                self.print_json("error", {"message": "No file data provided."})
                return
            media_path = self.pstatus['current'].get("path", "")
            if not media_path:
                self.print_json("error", {"message": "No media path provided."})
                return
            # 현재 이미지가 표시 중이면 숨김
            if self.pstatus['current'].get("is_image", True):
                self.show_image(media_path.strip())
            else:
                self.hide_image()
                self.set_media(media_path.strip())
                self.player.play()
        elif command == 'play':
            if self.pstatus['current'].get("is_image", True):
                self.show_image(self.pstatus['current'].get("path", ""))
            else:
                self.player.play()
        elif command == 'stop':
            if self.pstatus['current'].get("is_image", True):
                self.hide_image()
            else:
                self.player.stop()
        elif command == 'pause':
                self.player.pause()
        elif command == 'resume':
            if not self.pstatus['current'].get("is_image", True):
                self.player.play()
        elif command == 'hide_image':
            self.hide_image()
        elif command == 'volume':
                self.player.audio_set_volume(data['volume'])
        elif command == 'position':
            self.player.set_position(data['position'])
        elif command == 'time':
            self.player.set_time(data['time'])
        elif command == 'speed':
            self.player.set_rate(data['speed'])
        elif command == 'fullscreen':
            self.set_fullscreen(data['fullscreen'])
        elif command == 'background_color':     
            self.set_background_color(data['color'])
            self.pstatus['background'] = data['color']
        elif command == 'logo':
            self.set_logo(data['path'].strip())
            self.pstatus["logo"]["path"] = os.path.normpath(data['path'].strip())
        elif command == 'show_logo':
            self.pstatus["logo"]["show"] = data['value']
        elif command == 'logo_size':
            self.pstatus["logo"]["width"] = data['width']
            self.pstatus["logo"]["height"] = data['height']
            self.show_logo(self.pstatus["logo"]["show"])
        elif command == 'get_audio_devices':
            audio_devices = self.player.get_audio_output_devices()
            audio_device = self.player.get_audio_output_device()
            if audio_devices:
                self.print_json("devices", {"audio_devices": audio_devices, "audio_device": audio_device})
            else:
                self.print_json("error", {"message": "No audio devices found."})
        elif command == 'set_audio_device':
            if 'device' not in data:
                self.print_json("error", {"message": "No audio device provided."})
                return
            audio_device = data['device']
            if not audio_device:
                self.print_json("error", {"message": "Invalid audio device."})
                return
            # Set the audio output device
            self.player.set_audio_output_device(audio_device)
            # 지정된 오디오 디바이스 확인하고 피드백하기
            current_device = self.player.get_audio_output_device()
            if current_device == audio_device:
                self.print_json("devices", {"audio_device": current_device})
            else:
                self.print_json("error", {"message": f"Failed to set audio device to {audio_device}."})
        elif command == 'initialize':
            self.pstatus = data.get("pstatus", {})
            if not isinstance(self.pstatus, dict):
                self.print_json("error", {"message": "Invalid pstatus format. Expected a JSON object."})
                return
            # 기본 설정 적용
            self.initUi()


    def set_fullscreen(self, fullscreen):
        try:
            if fullscreen:
                self.showFullScreen()
            else:
                self.showNormal()
            self.player.set_fullscreen(fullscreen)
            self.pstatus['player']['fullscreen'] = fullscreen
            self.player.set_hwnd(int(self.winId()))
            self.update_player_data(None)  # 또는 그냥 self.update_player_data()
        except Exception as e:
            self.print_json("error", {"message": f"Error setting fullscreen: {e}"})

    def set_background_color(self, color):
        try:
            # Set background color
            self.setStyleSheet(f"background-color: {color};")
            self.print_json("default", {"background_color": color})
        except Exception as e:
            self.print_json("error", {"message": f"Error setting background color: {e}"})

    def set_logo(self, logo_path):
        try:
            # Set logo path
            if not logo_path or logo_path == "":
                self.print_json("error", {"message": "No logo path provided."})
                return
            self.logo_path = os.path.normpath(logo_path.strip())
            self.print_json("default", {"logo_path": self.logo_path})
        except Exception as e:
            self.print_json("error", {"message": f"Error setting logo: {e}"})
            
    def show_logo(self, value):
        try:
            logo_path = self.pstatus["logo"]["path"]
            if not logo_path or not os.path.isfile(logo_path):
                self.logo_label.setVisible(False)
                self.svg_widget.setVisible(False)
                return
            ext = os.path.splitext(logo_path)[1].lower()
            width = self.pstatus["logo"].get("width", 0)
            height = self.pstatus["logo"].get("height", 0)
            if ext == ".svg":
                self.logo_label.setVisible(False)
                self.svg_widget.load(logo_path)
                self.svg_widget.setVisible(value)
                self.svg_widget.raise_()
                if width == 0 or height == 0:
                    self.svg_widget.adjustSize()
                    self.svg_widget.move(
                        (self.width() - self.svg_widget.width()) // 2,
                        (self.height() - self.svg_widget.height()) // 2
                    )
                else:
                    self.svg_widget.resize(width, height)
                    self.svg_widget.move(
                        (self.width() - width) // 2,
                        (self.height() - height) // 2
                    )
            else:
                pixmap = QPixmap(logo_path)
                if pixmap.isNull():
                    self.logo_label.setVisible(False)
                    self.svg_widget.setVisible(False)
                    return
                self.svg_widget.setVisible(False)
                self.logo_label.setPixmap(
                    pixmap if width == 0 or height == 0 else pixmap.scaled(
                        width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                )
                if width == 0 or height == 0:
                    self.logo_label.resize(pixmap.width(), pixmap.height())
                    self.logo_label.move(
                        (self.width() - pixmap.width()) // 2,
                        (self.height() - pixmap.height()) // 2
                    )
                else:
                    self.logo_label.resize(width, height)
                    self.logo_label.move(
                        (self.width() - width) // 2,
                        (self.height() - height) // 2
                    )
                self.logo_label.setVisible(value)
                self.logo_label.raise_()
                self.print_json("info", self.pstatus)
        except Exception as e:
            self.print_json("error", {"message": f"Error showing logo: {e}"})

    def show_image(self, image_path):
        """
        이미지를 화면에 표시합니다.
        """
        try:
            if not image_path or not os.path.isfile(image_path):
                self.print_json("error", {"message": "Invalid image path or file not found."})
                return
            
            # 동영상 플레이어 중지
            if self.player.is_playing():
                self.player.stop()
            
            # 이미지 확장자 확인
            ext = os.path.splitext(image_path)[1].lower()
            
            # SVG 이미지 처리
            if ext == ".svg":
                self.image_label.setVisible(False)
                self.svg_widget.load(image_path)
                self.svg_widget.adjustSize()
                self.svg_widget.move(
                    (self.width() - self.svg_widget.width()) // 2,
                    (self.height() - self.svg_widget.height()) // 2
                )
                self.svg_widget.setVisible(True)
                self.svg_widget.raise_()
            # 일반 이미지 처리
            else:
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    self.print_json("error", {"message": "Failed to load image."})
                    return
                
                self.svg_widget.setVisible(False)
                
                # 화면 크기에 맞게 이미지 조정
                screen_size = self.size()
                scaled_pixmap = pixmap.scaled(
                    screen_size.width(), 
                    screen_size.height(),
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.resize(scaled_pixmap.size())
                self.image_label.move(
                    (self.width() - scaled_pixmap.width()) // 2,
                    (self.height() - scaled_pixmap.height()) // 2
                )
                self.image_label.setVisible(True)
                self.image_label.raise_()
            
            # 플레이어 데이터 업데이트
            self.update_player_data()
            
        except Exception as e:
            self.print_json("error", {"message": f"Error showing image: {e}"})
    
    def hide_image(self):
        """
        이미지를 화면에서 숨깁니다.
        """
        try:
            self.image_label.setVisible(False)
            self.svg_widget.setVisible(False)
            
            # 플레이어 데이터 업데이트
            self.update_player_data()
            
        except Exception as e:
            self.print_json("error", {"message": f"Error hiding image: {e}"})

    def set_media(self, media_path):
        try:
            # Set the media file
            if not media_path or media_path == "":
                self.print_json("error", {"message": "No media path provided."})
                return
                
            # 현재 이미지가 표시 중이면 숨김
            if self.pstatus['current'].get("is_image", False):
                self.hide_image()
                
            # 미디어 경로 정규화 및 설정
            self.pstatus['player']['media_path'] = media_path.strip()
            self.player.set_media(self.instance.media_new(self.pstatus['player']['media_path']))
            self.print_json("info", self.pstatus)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting media: {e}"})

    def resizeEvent(self, event):
        # 로고 위치 조정 코드
        # ...existing code...
        
        # 이미지가 표시 중이면 크기 재조정
        # player_data에 is_image, image_path 키가 없을 수 있으니 get으로 안전하게 접근
        is_image = self.pstatus['current'].get("is_image", False)
        image_path = self.pstatus['current'].get("path", "")
        if is_image and image_path:
            if os.path.splitext(image_path)[1].lower() == ".svg":
                if self.svg_widget.isVisible():
                    self.svg_widget.adjustSize()
                    self.svg_widget.move(
                        (self.width() - self.svg_widget.width()) // 2,
                        (self.height() - self.svg_widget.height()) // 2
                    )
            else:
                if self.image_label.isVisible() and self.image_label.pixmap():
                    original_pixmap = QPixmap(image_path)
                    screen_size = self.size()
                    scaled_pixmap = original_pixmap.scaled(
                        screen_size.width(),
                        screen_size.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    self.image_label.resize(scaled_pixmap.size())
                    self.image_label.move(
                        (self.width() - scaled_pixmap.width()) // 2,
                        (self.height() - scaled_pixmap.height()) // 2
                    )

        super().resizeEvent(event)
    
    def closeEvent(self, event):
        self.player.stop()
        if hasattr(self, 'stdin_thread'):
            self.stdin_thread.running = False
        event.accept()
        
    def print_json(self, type, data):
        # Print player data as JSON (single line, UTF-8) for Node.js to easily parse
        try:
            output = {
                "type": type,
                "data": data
            }
            json_data = json.dumps(output, ensure_ascii=False, separators=(",", ":"))
            print(json_data, flush=True)
        except Exception as e:
            # Avoid recursion if print_json fails
            print(json.dumps({"type": "error", "data": {"message": f"Error printing JSON: {e}"}}), flush=True)


if __name__ == "__main__":
    # 환경변수로 전달된 pStatus 받기 (없으면 None)
    import os
    vp_pstatus_json = os.environ.get("VP_PSTATUS")
    pstatus = None
    if vp_pstatus_json:
        try:
            import json
            pstatus = json.loads(vp_pstatus_json)
        except Exception as e:
            print(f"Failed to parse VP_PSTATUS: {e}", flush=True)
    app = QApplication(sys.argv)
    player = Player(pstatus=pstatus)
    player.show()
    sys.exit(app.exec())

