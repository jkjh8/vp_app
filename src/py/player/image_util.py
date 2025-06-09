from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

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
    if self.image_timer_instance.isActive():
        self.image_timer_instance.stop()
        self.print("debug", "Existing image timer stopped.")
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
            
def set_image_time(self, time):
    self.image_time = time
    self.print("set_image_time", {"image_time" : self.image_time})
    