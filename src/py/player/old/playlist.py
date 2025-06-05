import os
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer

def set_playlist_mode(player, mode = False):
    """
    플레이리스트 모드를 설정합니다.
    """
    if mode == 'true':
        mode = True
    player.pstatus['playlist_mode'] = mode
    player.print_json("playlist_mode", {"mode": mode})

def set_playlist(player, playlist, current_index=0):
    """
    플레이리스트를 설정하고 첫 번째 파일을 미리 로드합니다.
    """
    player.playlist = playlist
    player.playlist_track_index = int(current_index)
    player.print_json("playlist_set", {
        "playlist": player.playlist,
        "current_index": player.playlist_track_index
    })

def set_playlist_index(player, index):
    """
    플레이리스트의 현재 인덱스를 설정합니다.
    """
    if not player.playlist:
        player.print_json("error", {"message": "플레이리스트가 비어있음"})
        return

    if index <= 0 or index >= len(player.playlist):
        player.print_json("error", {"message": "잘못된 인덱스"})
        return

    player.playlist_track_index = int(index)
    player.print_json("playlist_index_set", {
        "index": index,
    })

    play_from_playlist(player, index)

def swap_players(player):
    """
    active/next 플레이어와 이미지 레이블을 스왑하고 트랜지션을 수행합니다.
    """
    player.active_player, player.next_player = player.next_player, player.active_player
    player.active_image_label, player.next_image_label = player.next_image_label, player.active_image_label

    # 다음 미디어가 이미지인 경우 바로 송출
    next_idx = (player.playlist_track_index + 1) % len(player.playlist) if player.playlist else None
    if next_idx is not None and 0 <= next_idx < len(player.playlist):
        next_file = player.playlist[next_idx]
        if is_image_file(next_file) and not is_video_file(next_file):
            player.show_image(next_file.get('path', ''))

    # 트랜지션 수행
    fade_transition(player, player.active_image_label, player.next_image_label)

    # 현재 미디어 정보를 반환
    media = ""
    if hasattr(player.active_player, "get_media") and player.active_player.get_media():
        media_obj = player.active_player.get_media()
        if hasattr(media_obj, "get_mrl") and media_obj.get_mrl():
            media = media_obj.get_mrl()

    # 현재 이미지 경로를 설정
    image_path = ""
    if player.playlist and 0 <= player.playlist_track_index < len(player.playlist):
        image_path = player.playlist[player.playlist_track_index].get('path', '')
    player.print_json("media_changed", {
        "media": media,
        "playlist_index": player.playlist_track_index,
        "image_path": image_path
    })

    # 추가 창 방지: active_player의 video_output을 동일한 winId로 설정
    if hasattr(player.active_player, "set_hwnd"):
        player.active_player.set_hwnd(player.winId)

def fade_transition(player, show_label, hide_label):
    """
    트랜지션 효과를 적용하여 레이블을 전환합니다.
    """
    show_label.setVisible(True)
    hide_label.setVisible(False)
    # 실제 구현 시 QGraphicsOpacityEffect 등을 사용하여 자연스러운 트랜지션 처리 가능

def preload_next_media(player, file):
    """
    다음 미디어를 next_player 또는 next_image_label에 미리 로드합니다.
    """
    path = file.get("path", "")
    mimetype = file.get("mimetype", "")
    ext = os.path.splitext(path)[1].lower()

    # 파일 유형 판별
    is_image = mimetype.startswith("image/") if mimetype else ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".svg"]
    is_video = mimetype.startswith("video/") if mimetype else ext in [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".webm"]
    is_audio = mimetype.startswith("audio/") if mimetype else ext in [".mp3", ".wav", ".aac", ".flac", ".ogg"]

    if is_image:
        # 이미지 파일을 미리 로드
        pixmap = QPixmap(path)
        player.next_image_label.setPixmap(pixmap)
        player.next_image_label.setVisible(False)
    elif is_video or is_audio:
        # 비디오/오디오 파일을 미리 로드
        media = player.next_player.get_instance().media_new(path)
        player.next_player.set_media(media)
    else:
        # 지원하지 않는 파일 형식 처리
        player.print_json("error", {"message": f"지원하지 않는 파일 형식: {path}"})

def handle_next_command(player, next_index=None):
    """
    다음 트랙으로 이동하거나 특정 인덱스로 이동합니다.
    """
    if not player.playlist:
        player.print_json("error", {"message": "플레이리스트가 비어있음"})
        return

    playlist_len = len(player.playlist)

    if next_index is not None:
        # 특정 인덱스로 이동
        if next_index == player.playlist_track_index + 1 or (player.playlist_track_index == playlist_len - 1 and next_index == 0):
            player.playlist_track_index = next_index % playlist_len
            swap_players(player)
            play_from_playlist(player, player.playlist_track_index)
        else:
            if next_index < 0 or next_index >= playlist_len:
                player.print_json("error", {"message": "잘못된 인덱스"})
                return
            player.playlist_track_index = next_index
            file = player.playlist[player.playlist_track_index]
            preload_next_media(player, file)
            swap_players(player)
            play_from_playlist(player, player.playlist_track_index)
    else:
        # 다음 트랙으로 이동
        player.playlist_track_index += 1
        if player.playlist_track_index >= playlist_len:
            player.playlist_track_index = 0
        swap_players(player)
        play_from_playlist(player, player.playlist_track_index)

def play_from_playlist(player, index=None):
    """
    플레이리스트에서 특정 인덱스의 파일을 재생합니다.
    """
    if not player.playlist:
        player.print_json("error", {"message": "playlist is empty", "tracks": player.playlist})
        return

    if index is not None:
        player.playlist_track_index = int(index)

    if player.playlist_track_index >= len(player.playlist):
        player.print_json("error", {"message": "Invalid index", "index": player.playlist_track_index, "playlist": player.playlist})
        return

    file = player.playlist[player.playlist_track_index]
    
    if is_image_file(file):
        # 이미지 파일 재생
        duration = file.get('duration') or file.get('time') or player.image_time
        try:
            duration = int(duration)
        except Exception:
            duration = 5
        player.pstatus['player']['duration'] = duration * 1000
        player.pstatus['player']['time'] = 0
        player.show_image(file['path'])
        player.print_json("player_data", player.pstatus['player'])

        # 이미지 타이머 설정
        if hasattr(player, '_image_timer') and player._image_timer:
            player._image_timer.stop()
            player._image_timer.deleteLater()
        player._image_timer = QTimer(player)
        player._image_timer.setInterval(500)

        def update_image_time():
            player.pstatus['player']['time'] += 500
            player.print_json("player_data", player.pstatus['player'])
            if player.pstatus['player']['time'] >= player.pstatus['player']['duration']:
                player._image_timer.stop()
                player._image_timer.deleteLater()
                player._image_timer = None
                if hasattr(player, 'handle_next_command'):
                    player.handle_next_command()

        player._image_timer.timeout.connect(update_image_time)
        player._image_timer.start()
    else:
        # 비디오/오디오 파일 재생
        player.set_media(file['path'])
        player.active_player.play()
    
    player.print_json("current_track", {"uuid": player.playlist[player.playlist_track_index].get('uuid', '')})

    # 다음 미디어 미리 로드
    preload_next_from_playlist(player)

def is_image_file(file):
    """
    파일이 이미지인지 확인합니다.
    """
    mimetype = file.get("mimetype", "")
    ext = os.path.splitext(file.get("path", ""))[1].lower()
    if mimetype:
        return mimetype.startswith("image/")
    return ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".svg"]

def is_video_file(file):
    """
    파일이 비디오인지 확인합니다.
    """
    mimetype = file.get("mimetype", "")
    ext = os.path.splitext(file.get("path", ""))[1].lower()
    if mimetype:
        return mimetype.startswith("video/")
    return ext in [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".webm"]


def preload_next_from_playlist(player):
    """
    플레이리스트에서 다음 파일을 미리 로드합니다.
    """
    idx = player.playlist_track_index + 1
    if player.playlist and idx < len(player.playlist):
        player.next_file = player.playlist[idx]
        preload_next_media(player, player.next_file)
    else:
        player.next_file = None
