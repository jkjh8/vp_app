from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
import os

def set_logo_center(player):
    """ 로고 위젯을 중앙에 위치시키고 크기를 조정합니다. """
    if not hasattr(player, 'logo_widget') or not player.logo_widget:
        player.print("error", "Logo widget is not initialized.")
        return
    logo_x = (player.width() - player.logo_width) // 2
    logo_y = (player.height() - player.logo_height) // 2
    player.logo_widget.setGeometry(logo_x, logo_y, player.logo_width, player.logo_height)
    player.logo_widget.setVisible(player.logo_show)

def set_logo_size(player, size):
    """ 로고 크기를 조정합니다. """
    try:
        player.logo_size = size
        update_logo_size(player)  # 새로운 크기 계산

        if not player.logo_svg and player.logo_widget and isinstance(player.logo_widget, QLabel):
            # Pixmap 로고의 경우 크기 조정된 Pixmap을 다시 설정
            pixmap = QPixmap(player.logo_file)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    player.logo_width,
                    player.logo_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                player.logo_widget.setPixmap(scaled_pixmap)

        set_logo_center(player)  # 크기와 위치 업데이트
    except Exception as e:
        player.print("error", f"Error setting logo size: {e}")

def update_logo_size(player):
    """ 로고 파일의 원본 크기를 확인하고 player.logo_width와 player.logo_height를 업데이트합니다. """
    if not player.logo_file or not os.path.exists(player.logo_file):
        player.print("error", "Logo file does not exist or path is empty.")
        return

    if player.logo_svg:
        # SVG 파일의 경우 QSvgRenderer를 사용하여 원본 크기를 가져옴
        try:
            svg_renderer = QSvgRenderer(player.logo_file)
            if not svg_renderer.isValid():
                player.print("error", "Failed to load SVG logo file.")
                return

            original_width = svg_renderer.defaultSize().width()
            original_height = svg_renderer.defaultSize().height()

            if player.logo_size > 0:
                player.logo_width = player.logo_size
                player.logo_height = int(original_height * (player.logo_size / original_width))
            else:
                player.logo_width = original_width
                player.logo_height = original_height

            player.print("debug", f"SVG logo size updated: width={player.logo_width}, height={player.logo_height}")
        except Exception as e:
            player.print("error", f"Error loading SVG logo: {e}")
    else:
        # Pixmap 파일의 경우 원본 크기를 확인
        pixmap = QPixmap(player.logo_file)
        if pixmap.isNull():
            player.print("error", "Failed to load Pixmap logo file.")
            return

        original_width = pixmap.width()
        original_height = pixmap.height()

        if player.logo_size > 0:
            player.logo_width = player.logo_size
            player.logo_height = int(original_height * (player.logo_size / original_width))
        else:
            player.logo_width = original_width
            player.logo_height = original_height

    player.print("debug", f"Logo size updated: width={player.logo_width}, height={player.logo_height}")

def set_logo_file(player, file):
    """ 로고 파일 경로를 설정하고 기존 로고를 제거한 뒤 새로운 로고 위젯을 초기화합니다. """
    if not file or not os.path.exists(file):
        player.print("error", f"Invalid logo file path: {file}")
        return

    # 기존 로고 위젯 제거
    if hasattr(player, 'logo_widget') and player.logo_widget:
        player.logo_widget.setVisible(False)  # 기존 로고 숨기기
        player.logo_widget.deleteLater()  # 기존 로고 위젯 삭제
        player.logo_widget = None
        player.print("debug", "Previous logo widget removed.")

    # 로고 파일 경로 및 관련 속성 업데이트
    player.logo_file = file
    player.logo_svg = player.logo_file.lower().endswith(".svg")
    player.print("debug", f"Logo file set to: {player.logo_file}")

    # 로고 크기 업데이트
    update_logo_size(player)

    # 로고 위젯 초기화
    if player.logo_svg:
        try:
            player.logo_widget = QSvgWidget(player.logo_file, player)
            player.print("debug", "SVG logo widget initialized successfully.")
        except Exception as e:
            player.print("error", f"Failed to initialize SVG logo widget: {e}")
            return
    else:
        try:
            pixmap = QPixmap(player.logo_file)
            if not pixmap.isNull():
                player.logo_widget = QLabel(player)  # 새로운 QLabel 생성
                player.logo_widget.setPixmap(
                    pixmap.scaled(
                        player.logo_width,
                        player.logo_height,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
                player.print("debug", "Pixmap logo widget initialized successfully.")
            else:
                player.print("error", "Pixmap is null. Failed to load image.")
                return
        except Exception as e:
            player.print("error", f"Failed to initialize Pixmap logo widget: {e}")
            return

    # 로고 위젯의 크기와 위치를 중앙으로 설정
    set_logo_center(player)


def set_logo_visibility(player, visible):
    """ 로고 위젯의 가시성을 설정합니다. """
    if hasattr(player, 'logo_widget') and player.logo_widget:
        player.logo_widget.setVisible(visible)
        player.print("debug", f"Logo visibility set to: {visible}")

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
        self.print("debug", "Previous logo widget removed.")

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
            self.print("debug", "SVG logo widget initialized successfully.")
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
                self.print("debug", "Pixmap logo widget initialized successfully.")
            else:
                self.print("error", "Pixmap is null. Failed to load image.")
                return
        except Exception as e:
            self.print("error", f"Failed to initialize Pixmap logo widget: {e}")
            return

    # 로고 위젯의 크기와 위치를 중앙으로 설정
    self.set_logo_center()
        
# 로고 위젯 위치 및 크기 조정
def set_logo_center(self):
    """ 로고 위젯을 중앙에 위치시키고 크기를 조정합니다. """
    if not hasattr(self, 'logo_widget') or not self.logo_widget:
        self.print("error", "Logo widget is not initialized.")
        return
    logo_x = (self.width() - self.logo_width) // 2
    logo_y = (self.height() - self.logo_height) // 2
    self.logo_widget.setGeometry(logo_x, logo_y, self.logo_width, self.logo_height)
    self.logo_widget.setVisible(self.logo_show)
    
# 로고 크기 조정
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