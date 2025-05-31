import os
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer

def swap_players(player):
    """
    active/next 포인터 스왑 및 트랜지션
    """
    player.active_player, player.next_player = player.next_player, player.active_player
    player.active_image_label, player.next_image_label = player.next_image_label, player.active_image_label
    # 현재 재생중인 파일 정보를 pstatus['current']에 반영
    playlist = player.pstatus.get('playlist', [])
    if playlist and 0 <= player.pstatus['playlistindex'] < len(playlist):
        player.pstatus['current'] = playlist[player.pstatus['playlistindex']]
        player.print_json("info", player.pstatus)
    # 다음 미디어가 이미지면 바로 송출
    next_idx = (player.pstatus['playlistindex'] + 1) % len(playlist) if playlist else None
    if next_idx is not None and 0 <= next_idx < len(playlist):
        next_file = playlist[next_idx]
        if is_image_file(next_file) and not is_video_file(next_file):
            player.show_image(next_file.get('path', ''))
    fade_transition(player, player.active_image_label, player.next_image_label)
    # 트랜지션후 변경된 미디어를 반환
    media = ""
    if hasattr(player.active_player, "get_media") and player.active_player.get_media():
        media_obj = player.active_player.get_media()
        if hasattr(media_obj, "get_mrl") and media_obj.get_mrl():
            media = media_obj.get_mrl()
    image_path = ""
    playlist = player.pstatus.get('playlist', [])
    if playlist and 0 <= player.pstatus['playlistindex'] < len(playlist):
        image_path = playlist[player.pstatus['playlistindex']].get('path', '')
    player.print_json("event", {
        "event": "media_changed",
        "media": media,
        "playlist_index": player.pstatus['playlistindex'],
        "image_path": image_path
    })

def fade_transition(player, show_label, hide_label):
    show_label.setVisible(True)
    hide_label.setVisible(False)
    # 실제 구현 시 QGraphicsOpacityEffect 등으로 자연스럽게 처리

def preload_next_media(player, file):
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
        player.next_image_label.setPixmap(pixmap)
        player.next_image_label.setVisible(False)
    elif is_video or is_audio:
        media = player.next_player.get_instance().media_new(path)
        player.next_player.set_media(media)
        # 재생하지 않고 대기
    else:
        player.print_json("error", {"message": f"지원하지 않는 파일 형식: {path}"})

def handle_next_command(player, next_index=None):
    playlist = player.pstatus.get('playlist', [])
    if not playlist:
        player.print_json("error", {"message": "플레이리스트가 비어있음"})
        return
    playlist_len = len(playlist)
    # next_index가 명시적으로 들어오면
    if next_index is not None:
        # next로 준비된 인덱스와 같으면 next 동작만 수행
        if next_index == player.pstatus['playlistindex'] + 1 or (player.pstatus['playlistindex'] == playlist_len - 1 and next_index == 0):
            player.pstatus['playlistindex'] = next_index % playlist_len
            swap_players(player)
            play_from_playlist(player, player.pstatus['playlistindex'])
        else:
            # 임의 인덱스면 해당 미디어를 미리 로딩 후 트랜지션
            if next_index < 0 or next_index >= playlist_len:
                player.print_json("error", {"message": "잘못된 인덱스"})
                return
            player.pstatus['playlistindex'] = next_index
            file = playlist[player.pstatus['playlistindex']]
            preload_next_media(player, file)
            swap_players(player)
            play_from_playlist(player, player.pstatus['playlistindex'])
    else:
        # 기존 next 동작
        player.pstatus['playlistindex'] += 1
        if player.pstatus['playlistindex'] >= playlist_len:
            player.pstatus['playlistindex'] = 0  # 마지막이면 첫번째로
        swap_players(player)
        play_from_playlist(player, player.pstatus['playlistindex'])

def play_from_playlist(player, index=None):
    playlist = player.pstatus.get('playlist', [])
    if not playlist:
        player.print_json("error", {"message": "플레이리스트가 비어있음"})
        return
    if index is not None:
        player.pstatus['playlistindex'] = index
    if player.pstatus['playlistindex'] < 0 or player.pstatus['playlistindex'] >= len(playlist):
        player.print_json("error", {"message": "잘못된 인덱스"})
        return
    file = playlist[player.pstatus['playlistindex']]
    # 현재 재생중인 파일 정보를 pstatus['current']에 반영
    player.pstatus['current'] = file
    player.print_json("info", player.pstatus)
    # 실제 재생
    if is_image_file(file):
        # 이미지 재생 시간 결정
        duration = file.get('duration') or file.get('time') or player.pstatus.get('image_time', 5)
        try:
            duration = int(duration)
        except Exception:
            duration = 5
        player.pstatus['player']['duration'] = duration * 1000  # ms 단위
        player.pstatus['player']['time'] = 0
        player.show_image(file['path'])
        # 이미지 타이머 시작 (1초마다 time 업데이트)
        if hasattr(player, '_image_timer') and player._image_timer:
            player._image_timer.stop()
            player._image_timer.deleteLater()
        player._image_timer = QTimer(player)
        player._image_timer.setInterval(500)  # 0.5초(500ms)로 변경
        def update_image_time():
            player.pstatus['player']['time'] += 500
            if player.pstatus['player']['time'] >= player.pstatus['player']['duration']:
                player._image_timer.stop()
                player._image_timer.deleteLater()
                player._image_timer = None
                # 다음 트랙으로 자동 이동
                if hasattr(player, 'handle_next_command'):
                    player.handle_next_command()
            # 0.5초마다 상태 업데이트
            from audio_device import update_player_data
            update_player_data(player)
        player._image_timer.timeout.connect(update_image_time)
        player._image_timer.start()
    else:
        # 비디오/오디오 파일은 기존 방식
        player.set_media(file['path'])
        player.active_player.play()
    # 다음 미디어 미리 프리로드
    preload_next_from_playlist(player)

def is_image_file(file):
    mimetype = file.get("mimetype", "")
    ext = os.path.splitext(file.get("path", ""))[1].lower()
    if mimetype:
        return mimetype.startswith("image/")
    return ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".svg"]

def is_video_file(file):
    mimetype = file.get("mimetype", "")
    ext = os.path.splitext(file.get("path", ""))[1].lower()
    if mimetype:
        return mimetype.startswith("video/")
    return ext in [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".webm"]

def set_playlist(player, playlist, current_index=0):
    player.pstatus['playlist'] = playlist
    player.pstatus['playlistindex'] = current_index
    preload_next_from_playlist(player)

def preload_next_from_playlist(player):
    playlist = player.pstatus.get('playlist', [])
    idx = player.pstatus['playlistindex'] + 1
    if playlist and idx < len(playlist):
        player.next_file = playlist[idx]
        preload_next_media(player, player.next_file)
    else:
        player.next_file = None
