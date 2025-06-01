import os
import sys
import win32process, win32con
import json
import vlc
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtSvgWidgets import QSvgWidget

from playlist import (
    swap_players, fade_transition, preload_next_media, handle_next_command,
    play_from_playlist, is_image_file, set_playlist, preload_next_from_playlist
)
from audio_device import initDoublePlayers, update_player_data
from handle_message import handle_message
from stdin import stdinReaderr

class Player(QMainWindow):
    def __init__(self, pstatus=None):
        super().__init__()
        self.pstatus = pstatus if pstatus else {}
        self.playlistmode = self.pstatus.get('playlistmode', False)
        self.setWindowTitle("VP")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("icon.png"))
        # 오디오 디바이스
        self.audioDevices = []
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
        initDoublePlayers(self)
        self.initStdinThread()
        self.initUi()
        try:
            handle = win32process.GetCurrentProcess()
            win32process.SetPriorityClass(handle, win32con.REALTIME_PRIORITY_CLASS)
        except Exception as e:
            self.print_json("error", {"message": f"우선순위 설정 실패: {e}"})

        self.next_file = None
        self.pending_logo_request = False  # 로고 표시 요청 플래그 추가

    def initUi(self):
        self.set_background_color(self.pstatus.get("background", "#ffffff"))
        self.set_fullscreen(self.pstatus.get("fullscreen", False))
        self.set_logo(self.pstatus.get("logo", {}).get("file", ""))
        self.show_logo(self.pstatus.get("logo", {}).get("show", False))

    def initStdinThread(self):
        # Initialize stdin thread
        self.stdin_thread = stdinReaderr()
        self.stdin_thread.message_received.connect(lambda data: handle_message(self, data))
        self.stdin_thread.start()

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
              # fullscreen 전환 후 로고와 이미지 위치 재조정을 위해 resizeEvent 호출
            # QTimer를 사용해서 화면 전환이 완료된 후 위치 조정
            QTimer.singleShot(100, self._adjust_widgets_position)
            
            update_player_data(self, None)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting fullscreen: {e}"})

    def _adjust_widgets_position(self):
        """로고와 이미지 위젯의 위치를 조정하는 헬퍼 메소드"""
        try:
            # 현재 표시되는 로고가 있으면 위치 재조정
            if self.pstatus.get('logo', {}).get('show', False):
                logo_path = self.pstatus["logo"].get("file", "")
                if logo_path and os.path.isfile(logo_path):
                    self.show_logo(True)  # 로고를 다시 표시하여 위치 재조정
            
            # 현재 표시되는 이미지가 있으면 위치 재조정
            is_image = self.pstatus['current'].get("is_image", False)
            image_path = self.pstatus['current'].get("path", "")
            if is_image and image_path:
                self.show_image(image_path)  # 이미지를 다시 표시하여 위치 재조정
        except Exception as e:
            self.print_json("error", {"message": f"Error adjusting widgets position: {e}"})

    def set_background_color(self, color):
        try:
            # Set background color
            self.setStyleSheet(f"background-color: {color};")
        except Exception as e:
            self.print_json("error", {"message": f"Error setting background color: {e}"})

    def set_logo(self, logo_path):
        try:
            # Set logo path
            self.pstatus["logo"]["file"] = logo_path.strip()
            self.show_logo(True)
        except Exception as e:
            self.print_json("error", {"message": f"Error setting logo: {e}"})
            
    def show_logo(self, value):
        # value가 None이거나 빈 문자열인 경우 False로 처리
        if value is None or value == "":
            value = False
        try:
            value = bool(value)
            self.pstatus["logo"]["show"] = value

            # 이미지 송출 중일 경우 로고 표시 요청을 큐에 저장
            is_image = self.pstatus['current'].get("is_image", False)
            if is_image and self.active_image_label.isVisible():
                self.pending_logo_request = value
                return

            # 로고 표시 로직
            logo_path = self.pstatus["logo"].get("file", "")
            if not value or not logo_path or not os.path.isfile(logo_path):
                self.logo_label.setVisible(False)
                self.svg_widget.setVisible(False)
                return

            ext = os.path.splitext(logo_path)[1].lower()
            width = self.pstatus["logo"].get("width", 0)
            height = self.pstatus["logo"].get("height", 0)

            if ext == ".svg":
                self.logo_label.setVisible(False)
                self.svg_widget.load(logo_path)
                self.svg_widget.setVisible(True)
                self.svg_widget.raise_()  # 로고를 최상위 레이어로 이동
                if width == 0 and height == 0:
                    self.svg_widget.adjustSize()
                    self.svg_widget.move(
                        (self.width() - self.svg_widget.width()) // 2,
                        (self.height() - self.svg_widget.height()) // 2
                    )
                elif width and height:
                    self.svg_widget.resize(width, height)
                    self.svg_widget.move(
                        (self.width() - width) // 2,
                        (self.height() - height) // 2
                    )
                else:
                    orig_size = self.svg_widget.sizeHint()
                    orig_w, orig_h = orig_size.width(), orig_size.height()
                    if width:
                        ratio = width / orig_w
                        new_w = width
                        new_h = int(orig_h * ratio)
                    elif height:
                        ratio = height / orig_h
                        new_w = int(orig_w * ratio)
                        new_h = height
                    else:
                        new_w, new_h = orig_w, orig_h
                    self.svg_widget.resize(new_w, new_h)
                    self.svg_widget.move(
                        (self.width() - new_w) // 2,
                        (self.height() - new_h) // 2
                    )
            else:
                pixmap = QPixmap(logo_path)
                if pixmap.isNull():
                    self.logo_label.setVisible(False)
                    self.svg_widget.setVisible(False)
                    return

                self.svg_widget.setVisible(False)
                orig_w, orig_h = pixmap.width(), pixmap.height()
                if width == 0 and height == 0:
                    scaled_pixmap = pixmap
                    new_w, new_h = orig_w, orig_h
                elif width and height:
                    scaled_pixmap = pixmap.scaled(
                        width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
                    )
                    new_w, new_h = width, height
                else:
                    if width:
                        ratio = width / orig_w
                        new_w = width
                        new_h = int(orig_h * ratio)
                    elif height:
                        ratio = height / orig_h
                        new_w = int(orig_w * ratio)
                        new_h = height
                    else:
                        new_w, new_h = orig_w, orig_h
                    scaled_pixmap = pixmap.scaled(
                        new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )

                self.logo_label.setPixmap(scaled_pixmap)
                self.logo_label.resize(new_w, new_h)
                self.logo_label.move(
                    (self.width() - new_w) // 2,
                    (self.height() - new_h) // 2
                )
                self.logo_label.setVisible(True)
                self.logo_label.raise_()  # 로고를 최상위 레이어로 이동

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
            update_player_data(self)
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
            update_player_data(self)

            # 이미지 숨김 후 로고 표시 요청이 있으면 처리
            if self.pending_logo_request:
                self.show_logo(self.pending_logo_request)
                self.pending_logo_request = False
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

    def resizeEvent(self, event):
        # 로고 위치 및 크기 조정
        if self.pstatus.get('logo', {}).get('show', False):
            logo_path = self.pstatus["logo"].get("file", "")
            if logo_path and os.path.isfile(logo_path):
                ext = os.path.splitext(logo_path)[1].lower()
                width = self.pstatus["logo"].get("width", 0)
                height = self.pstatus["logo"].get("height", 0)
                
                if ext == ".svg":
                    if self.svg_widget.isVisible():
                        if width == 0 and height == 0:
                            # 원본 크기 유지
                            self.svg_widget.adjustSize()
                            self.svg_widget.move(
                                (self.width() - self.svg_widget.width()) // 2,
                                (self.height() - self.svg_widget.height()) // 2
                            )
                        elif width and height:
                            # 지정된 크기로 설정
                            self.svg_widget.resize(width, height)
                            self.svg_widget.move(
                                (self.width() - width) // 2,
                                (self.height() - height) // 2
                            )
                        else:
                            # 비율 유지하며 크기 조정
                            orig_size = self.svg_widget.sizeHint()
                            orig_w, orig_h = orig_size.width(), orig_size.height()
                            if orig_w > 0 and orig_h > 0:
                                if width:
                                    ratio = width / orig_w
                                    new_w = width
                                    new_h = int(orig_h * ratio)
                                elif height:
                                    ratio = height / orig_h
                                    new_w = int(orig_w * ratio)
                                    new_h = height
                                else:
                                    new_w, new_h = orig_w, orig_h
                                self.svg_widget.resize(new_w, new_h)
                                self.svg_widget.move(
                                    (self.width() - new_w) // 2,
                                    (self.height() - new_h) // 2
                                )
                else:
                    if self.logo_label.isVisible() and self.logo_label.pixmap():
                        pixmap = QPixmap(logo_path)
                        if not pixmap.isNull():
                            orig_w, orig_h = pixmap.width(), pixmap.height()
                            if width == 0 and height == 0:
                                # 원본 크기 유지
                                scaled_pixmap = pixmap
                                new_w, new_h = orig_w, orig_h
                            elif width and height:
                                # 지정된 크기로 설정 (비율 무시)
                                scaled_pixmap = pixmap.scaled(
                                    width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
                                )
                                new_w, new_h = width, height
                            else:
                                # 비율 유지하며 크기 조정
                                if width:
                                    ratio = width / orig_w
                                    new_w = width
                                    new_h = int(orig_h * ratio)
                                elif height:
                                    ratio = height / orig_h
                                    new_w = int(orig_w * ratio)
                                    new_h = height
                                else:
                                    new_w, new_h = orig_w, orig_h
                                scaled_pixmap = pixmap.scaled(
                                    new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                                )
                            self.logo_label.setPixmap(scaled_pixmap)
                            self.logo_label.resize(new_w, new_h)
                            self.logo_label.move(
                                (self.width() - new_w) // 2,
                                (self.height() - new_h) // 2
                            )
        
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

