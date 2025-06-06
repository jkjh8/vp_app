def set_background_color(self, color):
        """ 배경 색상을 설정하는 함수 """
        self.background_color = color
        self.setStyleSheet(f"background-color: {self.background_color};")  # 메인 윈도우 배경색 변경
        for widget in self.player_widgets:
            widget.setStyleSheet(f"background-color: {self.background_color};")
        self.print("debug", f"Background color set to {self.background_color}")
