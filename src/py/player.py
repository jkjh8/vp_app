import os
import sys
import win32process, win32con
import json
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget
import functools

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
        self.playlistmode = self.pstatus.get('playlistmode', False)
        self.setWindowTitle("VP")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))
        # 더블버퍼 플레이어 및 이미지 레이블
        self.playerA = None
        self.playerB = None
        self.active_player = None
        self.next_player = None
        self.image_labelA = QLabel(self)
        self.image_labelA.setVisible(False)
        self.image_labelA.setAlignment(Qt.AlignCenter)
        self.image_labelA.setStyleSheet("background: transparent;")
        self.image_labelB = QLabel(self)
        self.image_labelB.setVisible(False)
        self.image_labelB.setAlignment(Qt.AlignCenter)
        self.image_labelB.setStyleSheet("background: transparent;")
        self.active_image_label = self.image_labelA
        self.next_image_label = self.image_labelB
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
        self.initDoublePlayers()
        self.initStdinThread()
        self.initUi()
        try:
            handle = win32process.GetCurrentProcess()
            win32process.SetPriorityClass(handle, win32con.REALTIME_PRIORITY_CLASS)
        except Exception as e:
            self.print_json("error", {"message": f"우선순위 설정 실패: {e}"})

        self.playlist_index = 0
        self.next_file = None

    def initUi(self):
        self.set_background_color(self.pstatus.get("background", "#ffffff"))
        self.set_fullscreen(self.pstatus.get("fullscreen", False))
        self.set_logo(self.pstatus.get("logo", {}).get("path", ""))
        self.show_logo(self.pstatus.get("logo", {}).get("show", False))

    def initStdinThread(self):
        # Initialize stdin thread
        self.stdin_thread = stdinReaderr()
        self.stdin_thread.message_received.connect(self.handle_message)
        self.stdin_thread.start()

    def initDoublePlayers(self):
        # VLC 인스턴스 2개 생성
        self.instanceA = vlc.Instance(
            "--no-video-title-show",
            "--avcodec-hw=any",
            "--no-drop-late-frames",
            "--no-skip-frames"
        )
        self.instanceB = vlc.Instance(
            "--no-video-title-show",
            "--avcodec-hw=any",
            "--no-drop-late-frames",
            "--no-skip-frames"
        )
        self.playerA = self.instanceA.media_player_new()
        self.playerB = self.instanceB.media_player_new()
        self.playerA.set_hwnd(int(self.winId()))
        self.playerB.set_hwnd(int(self.winId()))
        self.active_player = self.playerA
        self.next_player = self.playerB
        # 이벤트 핸들러 등록
        self.init_events_double()

    # def init_events(self):
    #     # 이벤트 등록하기
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerTimeChanged, self.update_player_data)
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerPlaying, self.update_player_data)
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerPaused, self.update_player_data)
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerStopped, self.update_player_data)
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, self.on_end_reached)
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEncounteredError, self.on_error)
    #     self.player.event_manager().event_attach(vlc.EventType.MediaPlayerMediaChanged, self.update_player_data)
        
    def init_events_double(self):
        try:
            self.print_json("message", {"message": "Initializing double player events"})
            event_types = [
                (vlc.EventType.MediaPlayerEndReached, self.on_end_reached),
                (vlc.EventType.MediaPlayerEncounteredError, self.on_error),
                (vlc.EventType.MediaPlayerTimeChanged, self.update_player_data),
                (vlc.EventType.MediaPlayerPlaying, self.update_player_data),
                (vlc.EventType.MediaPlayerPaused, self.update_player_data),
                (vlc.EventType.MediaPlayerStopped, self.update_player_data),
                (vlc.EventType.MediaPlayerMediaChanged, self.update_player_data),
            ]
            for player in [self.playerA, self.playerB]:
                em = player.event_manager()
                for event_type, handler in event_types:
                    em.event_attach(event_type, self._make_event_handler(handler, player))
        except Exception as e:
            self.print_json("error", {"message": f"Error initializing double player events: {e}"})

    def _make_event_handler(self, handler, which_player):
        def event_handler(event):
            event._which_player = which_player
            handler(event)
        return event_handler

    def on_end_reached(self, event):
        try:
            self.print_json("message", {"message": "End reached event triggered"})
            self.update_player_data(event)
            # 단일 파일 모드(playlistmode == False)에서도 end 이벤트가 오면 stop 이벤트 발생
            if not self.playlistmode:
                self.print_json("stop", {"message": "재생이 중지되었습니다."})
                return
            repeat_mode = self.pstatus.get('repeat', 'none')
            playlist = self.pstatus.get('playlist', [])
            # single: 현재 곡/파일만 반복
            if repeat_mode == 'single':
                self.active_player.stop()
                self.active_player.play()
            # all: 리스트 끝이면 중지, 아니면 next
            elif repeat_mode == 'all':
                if self.playlist_index + 1 < len(playlist):
                    self.handle_next_command(self.playlist_index + 1)
                else:
                    self.print_json("info", {"message": "플레이리스트 끝 (all)"})
                    self.print_json("stop", {"message": "재생이 중지되었습니다."})
            # all_repeat: 리스트 끝이면 처음으로, 아니면 next
            elif repeat_mode == 'all_repeat':
                if self.playlist_index + 1 < len(playlist):
                    self.handle_next_command(self.playlist_index + 1)
                else:
                    self.handle_next_command(0)
            # none: 하나만 재생하고 중지
            elif repeat_mode == 'none':
                self.print_json("info", {"message": "재생 완료 (none)"})
                self.print_json("stop", {"message": "재생이 중지되었습니다."})
            else:
                # 기본 동작: all과 동일
                if self.playlist_index + 1 < len(playlist):
                    self.handle_next_command(self.playlist_index + 1)
                else:
                    self.print_json("info", {"message": "플레이리스트 끝 (default)"})
                    self.print_json("stop", {"message": "재생이 중지되었습니다."})
        except Exception as e:
            self.print_json("error", {"message": f"Exception in on_end_reached: {e}"})

    def on_error(self, event):
        self.print_json("error", {"message": "Error occurred"})

    def update_player_data(self, event=None):
        # 이벤트가 있으면 어떤 플레이어에서 발생했는지 확인
        player = getattr(event, "_which_player", None) if event is not None else self.active_player
        # 현재 활성 플레이어만 처리
        if player != self.active_player:
            return
        event_type = getattr(event, "type", "manual") if event is not None else "manual"
        self.pstatus.setdefault('player', {})
        self.pstatus['player']['event'] = str(event_type)
        media = self.active_player.get_media()
        if media is not None:
            self.pstatus['player']['filename'] = media.get_mrl()
        else:
            self.pstatus['player']['filename'] = ""
        self.pstatus['player']['duration'] = self.active_player.get_length()
        self.pstatus['player']['time'] = self.active_player.get_time()
        self.pstatus['player']['position'] = self.active_player.get_position()
        self.pstatus['player']['playing'] = self.active_player.is_playing()
        self.pstatus['player']['volume'] = self.active_player.audio_get_volume()
        self.pstatus['player']['speed'] = self.active_player.get_rate()
        self.pstatus['player']['fullscreen'] = self.active_player.get_fullscreen()
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
            self.pstatus['current'] = file
            if not self.pstatus['current']:
                self.print_json("error", {"message": "No file data provided."})
                return
            if not self.pstatus['current'].get("is_image", True):
                media_path = self.pstatus['current'].get("path", "")
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
                self.active_player.play()
        elif command == 'play':
            if self.pstatus['current'].get("is_image", True):
                self.show_image(self.pstatus['current'].get("path", ""))
            else:
                self.active_player.play()
        elif command == 'stop':
            if self.pstatus['current'].get("is_image", True):
                self.hide_image()
            else:
                self.active_player.stop()
        elif command == 'pause':
            self.active_player.pause()
        elif command == 'resume':
            if not self.pstatus['current'].get("is_image", True):
                self.active_player.play()
        elif command == 'hide_image':
            self.hide_image()
        elif command == 'volume':
            self.active_player.audio_set_volume(data['volume'])
        elif command == 'position':
            self.active_player.set_position(data['position'])
        elif command == 'time':
            self.active_player.set_time(data['time'])
        elif command == 'speed':
            self.active_player.set_rate(data['speed'])
        elif command == 'fullscreen':
            self.set_fullscreen(data['fullscreen'])
        elif command == 'background_color':     
            self.set_background_color(data['color'])
            self.pstatus['background'] = data['color']
        elif command == 'logo':
            self.set_logo(data['path'].strip())
            self.pstatus.setdefault("logo", {})["path"] = os.path.normpath(data['path'].strip())
        elif command == 'show_logo':
            self.pstatus.setdefault("logo", {})["show"] = data['value']
            self.show_logo(self.pstatus["logo"]["show"])
        elif command == 'logo_size':
            self.pstatus.setdefault("logo", {})["width"] = data['width']
            self.pstatus.setdefault("logo", {})["height"] = data['height']
            self.show_logo(self.pstatus["logo"].get("show", False))
        elif command == 'get_audio_devices':
            audio_devices = self.active_player.get_audio_output_devices()
            audio_device = self.active_player.get_audio_output_device()
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
            self.active_player.set_audio_output_device(audio_device)
            # 지정된 오디오 디바이스 확인하고 피드백하기
            current_device = self.active_player.get_audio_output_device()
            if current_device == audio_device:
                self.print_json("devices", {"audio_device": current_device})
            else:
                self.print_json("error", {"message": f"Failed to set audio device to {audio_device}."})
        elif command == 'initialize':
            new_pstatus = data.get("pstatus", {})
            if not isinstance(new_pstatus, dict):
                self.print_json("error", {"message": "Invalid pstatus format. Expected a JSON object."})
                return
            self.update_pstatus_except_player(new_pstatus)
            self.initUi()
        elif command == 'pstatus':
            new_pstatus = data.get("pstatus", {})
            if isinstance(new_pstatus, dict):
                # 기존 pstatus의 'player' 값은 유지, 나머지만 업데이트
                player_data = self.pstatus.get("player", {})
                self.pstatus = {k: v for k, v in new_pstatus.items() if k != "player"}
                self.pstatus["player"] = player_data
            else:
                self.print_json("error", {"message": "Invalid pstatus format. Expected a JSON object."})
                return
            if not isinstance(self.pstatus, dict):
                self.print_json("error", {"message": "Invalid pstatus format. Expected a JSON object."})
                return
        elif command == 'playlist':
            # playlist 전체 변경
            playlist = data.get("playlist", [])
            current_index = data.get("index", 0)
            self.set_playlist(playlist, current_index)
        elif command == 'next':
            # next 명령, 인덱스가 있으면 해당 인덱스로 이동
            next_index = data.get("index")
            self.handle_next_command(next_index)


    def set_fullscreen(self, fullscreen):
        try:
            if fullscreen:
                self.showFullScreen()
            else:
                self.showNormal()
            # 모든 플레이어에 적용
            if hasattr(self, 'playerA') and self.playerA:
                self.playerA.set_fullscreen(fullscreen)
            if hasattr(self, 'playerB') and self.playerB:
                self.playerB.set_fullscreen(fullscreen)
            self.pstatus['player']['fullscreen'] = fullscreen
            if hasattr(self, 'playerA') and self.playerA:
                self.playerA.set_hwnd(int(self.winId()))
            if hasattr(self, 'playerB') and self.playerB:
                self.playerB.set_hwnd(int(self.winId()))
            self.update_player_data(None)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting fullscreen: {e}"})

    def set_background_color(self, color):
        try:
            # Set background color
            self.setStyleSheet(f"background-color: {color};")
            self.print_json("message", {"background_color": color})
        except Exception as e:
            self.print_json("error", {"message": f"Error setting background color: {e}"})

    def set_logo(self, logo_path):
        try:
            # Set logo path
            if not logo_path or logo_path == "":
                self.print_json("error", {"message": "No logo path provided."})
                return
            self.logo_path = os.path.normpath(logo_path.strip())
            self.print_json("message", {"logo_path": self.logo_path})
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
            if self.active_player and self.active_player.is_playing():
                self.active_player.stop()
            # SVG 이미지 처리
            ext = os.path.splitext(image_path)[1].lower()
            if ext == ".svg":
                self.active_image_label.setVisible(False)
                self.svg_widget.load(image_path)
                self.svg_widget.adjustSize()
                self.svg_widget.move(
                    (self.width() - self.svg_widget.width()) // 2,
                    (self.height() - self.svg_widget.height()) // 2
                )
                self.svg_widget.setVisible(True)
                self.svg_widget.raise_()
            else:
                pixmap = QPixmap(image_path)
                if pixmap.isNull():
                    self.print_json("error", {"message": "Failed to load image."})
                    return
                self.svg_widget.setVisible(False)
                screen_size = self.size()
                scaled_pixmap = pixmap.scaled(
                    screen_size.width(),
                    screen_size.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.active_image_label.setPixmap(scaled_pixmap)
                self.active_image_label.resize(scaled_pixmap.size())
                self.active_image_label.move(
                    (self.width() - scaled_pixmap.width()) // 2,
                    (self.height() - scaled_pixmap.height()) // 2
                )
                self.active_image_label.setVisible(True)
                self.active_image_label.raise_()
            self.update_player_data()
        except Exception as e:
            self.print_json("error", {"message": f"Error showing image: {e}"})

    def hide_image(self):
        """
        현재 표시 중인 이미지를 숨깁니다.
        """
        try:
            self.active_image_label.setVisible(False)
            self.next_image_label.setVisible(False)
            self.svg_widget.setVisible(False)
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
            if self.active_player:
                self.active_player.set_media(self.active_player.get_instance().media_new(self.pstatus['player']['media_path']))
            self.print_json("info", self.pstatus)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting media: {e}"})

    def swap_players(self):
        # active/next 포인터 스왑 및 트랜지션
        self.active_player, self.next_player = self.next_player, self.active_player
        self.active_image_label, self.next_image_label = self.next_image_label, self.active_image_label
        # 현재 재생중인 파일 정보를 pstatus['current']에 반영
        playlist = self.pstatus.get('playlist', [])
        if playlist and 0 <= self.playlist_index < len(playlist):
            self.pstatus['current'] = playlist[self.playlist_index]
            self.print_json("info", self.pstatus)
        # 트랜지션(페이드 등) 예시
        self.fade_transition(self.active_image_label, self.next_image_label)

    def fade_transition(self, show_label, hide_label):
        # 간단한 페이드 트랜지션 예시 (QPropertyAnimation 활용 가능)
        show_label.setVisible(True)
        hide_label.setVisible(False)
        # 실제 구현 시 QGraphicsOpacityEffect 등으로 자연스럽게 처리

    def preload_next_media(self, file):
        """
        다음 미디어를 next_player/next_image_label에 미리 로딩
        file: dict, 최소한 'path' 필드 필요, 가능하면 'mimetype' 포함
        """
        path = file.get("path", "")
        mimetype = file.get("mimetype", "")
        ext = os.path.splitext(path)[1].lower()
        is_image = False
        is_video = False
        is_audio = False
        # mimetype 우선 판별
        if mimetype:
            if mimetype.startswith("image/"):
                is_image = True
            elif mimetype.startswith("video/"):
                is_video = True
            elif mimetype.startswith("audio/"):
                is_audio = True
        else:
            # 확장자로 판별
            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".svg"]:
                is_image = True
            elif ext in [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".webm"]:
                is_video = True
            elif ext in [".mp3", ".wav", ".aac", ".flac", ".ogg"]:
                is_audio = True
        if is_image:
            pixmap = QPixmap(path)
            self.next_image_label.setPixmap(pixmap)
            self.next_image_label.setVisible(False)
        elif is_video or is_audio:
            media = self.next_player.get_instance().media_new(path)
            self.next_player.set_media(media)
            # 재생하지 않고 대기
        else:
            self.print_json("error", {"message": f"지원하지 않는 파일 형식: {path}"})

    def handle_next_command(self, next_index=None):
        playlist = self.pstatus.get('playlist', [])
        if not playlist:
            self.print_json("error", {"message": "플레이리스트가 비어있음"})
            return
        # next_index가 명시적으로 들어오면
        if next_index is not None:
            # next로 준비된 인덱스와 같으면 next 동작만 수행
            if next_index == self.playlist_index + 1:
                self.playlist_index = next_index
                self.swap_players()
                self.play_from_playlist(self.playlist_index)
            else:
                # 임의 인덱스면 해당 미디어를 미리 로딩 후 트랜지션
                if next_index < 0 or next_index >= len(playlist):
                    self.print_json("error", {"message": "잘못된 인덱스"})
                    return
                self.playlist_index = next_index
                file = playlist[self.playlist_index]
                self.preload_next_media(file)
                self.swap_players()
                self.play_from_playlist(self.playlist_index)
        else:
            # 기존 next 동작
            self.playlist_index += 1
            if self.playlist_index >= len(playlist):
                self.print_json("info", {"message": "플레이리스트 끝"})
                return
            self.swap_players()
            self.play_from_playlist(self.playlist_index)

    def play_from_playlist(self, index=None):
        playlist = self.pstatus.get('playlist', [])
        if not playlist:
            self.print_json("error", {"message": "플레이리스트가 비어있음"})
            return
        if index is not None:
            self.playlist_index = index
        if self.playlist_index < 0 or self.playlist_index >= len(playlist):
            self.print_json("error", {"message": "잘못된 인덱스"})
            return
        file = playlist[self.playlist_index]
        # 현재 재생중인 파일 정보를 pstatus['current']에 반영
        self.pstatus['current'] = file
        self.print_json("info", self.pstatus)
        # 실제 재생
        if self.is_image_file(file):
            self.show_image(file['path'])
        else:
            self.set_media(file['path'])
            self.active_player.play()
        # 다음 미디어 미리 프리로드
        self.preload_next_from_playlist()

    def is_image_file(self, file):
        mimetype = file.get("mimetype", "")
        ext = os.path.splitext(file.get("path", ""))[1].lower()
        if mimetype:
            return mimetype.startswith("image/")
        return ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".svg"]

    def set_playlist(self, playlist, current_index=0):
        self.pstatus['playlist'] = playlist
        self.playlist_index = current_index
        self.preload_next_from_playlist()

    def preload_next_from_playlist(self):
        playlist = self.pstatus.get('playlist', [])
        idx = self.playlist_index + 1
        if playlist and idx < len(playlist):
            self.next_file = playlist[idx]
            self.preload_next_media(self.next_file)
        else:
            self.next_file = None

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
        if self.active_player:
            self.active_player.stop()
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

