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
