from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

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
            
def set_image_time(self, time):
    self.image_time = time
    self.print("set_image_time", {"value" : self.image_time})

def update_widget_sizes(self, event):
    """ MainWindow 크기 변경 시 위젯 크기를 업데이트합니다. 각위젯에 이미지가 있으면 함께 크기를 조정합니다. """
    for player in self.player_widgets:
        player.setGeometry(0, 0, self.width(), self.height())
        # 이미지 위젯이 있다면 크기를 조정합니다.
    self.update_image_size()