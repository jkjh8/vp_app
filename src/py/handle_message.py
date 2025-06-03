import json
import os
from player_instance import get_audio_devices, set_audio_device
from playlist import set_playlist, set_playlist_mode, set_playlist_index

# --- 개별 명령 처리 함수들 ---
def handle_set(player, data):
    file = data.get("file", {})
    player.pstatus['current'] = file
    if not file:
        player.print_json("error", {"message": "No file data provided."})
        return
    if not file.get("is_image", True):
        media_path = file.get("path", "")
        if not media_path:
            player.print_json("error", {"message": "No media path provided."})
            return
        player.set_media(media_path.strip())

def handle_playid(player, data):
    file = data.get("file", {})
    player.pstatus['current'] = file
    if not file:
        player.print_json("error", {"message": "No file data provided."})
        return
    media_path = file.get("path", "")
    if not media_path:
        player.print_json("error", {"message": "No media path provided."})
        return
    if file.get("is_image", True):
        player.show_image(media_path.strip())
    else:
        player.hide_image()
        player.set_media(media_path.strip())
        player.active_player.play()

def handle_repeat(player, data):
    repeat_mode = data.get("mode", "none")
    if repeat_mode not in ['none', 'single', 'all', 'repeat_one']:
        player.print_json("error", {"message": "Invalid repeat mode."})
        return
    player.pstatus['repeat'] = repeat_mode
    player.print_json("message", f"Repeat mode set to {repeat_mode}")

def update_pstatus(player, data):
    new_pstatus = data.get("pstatus", {})
    if isinstance(new_pstatus, dict):
        # 기존 player, current 값을 유지하면서 나머지만 업데이트
        for k, v in new_pstatus.items():
            if k not in ("player", "current"):
                player.pstatus[k] = v
    else:
        player.print_json("error", {"message": "Invalid pstatus format. Expected a JSON object."})

def set_image_time(player, data):
    player.image_time = data.get('time', 10)
    player.print_json("set_image_time", {"image_time": player.image_time})

# --- 메인 메시지 핸들러 ---
def handle_message(player, data):
    player.receive_udp_data = data.strip()
    try:
        data = json.loads(player.receive_udp_data)
    except Exception:
        player.print_json("error", {"message": "Invalid JSON."})
        return
    if not isinstance(data, dict):
        player.print_json("error", {"message": "Invalid data format. Expected a JSON object."})
        return
    command = data.get("command")
    if not command:
        player.print_json("error", {"message": "Missing 'command' in data."})
        return

    dispatch = {
        # set media or image
        'set': lambda: handle_set(player, data),
        'playid': lambda: handle_playid(player, data),
        # player control commands
        'play': lambda: player.show_image(player.pstatus['current'].get("path", "")) if player.pstatus['current'].get("is_image", True) else player.active_player.play(),
        'stop': lambda: player.hide_image() if player.pstatus['current'].get("is_image", True) else player.active_player.stop(),
        'pause': lambda: player.active_player.pause(),
        'resume': lambda: player.active_player.play() if not player.pstatus['current'].get("is_image", True) else None,
        'volume': lambda: player.active_player.audio_set_volume(data['volume']),
        'position': lambda: player.active_player.set_position(data['position']),
        'time': lambda: player.active_player.set_time(data['time']),
        'speed': lambda: player.active_player.set_rate(data['speed']),
        'get_audio_devices': lambda: get_audio_devices(player),
        'set_audio_device': lambda: set_audio_device(player, data.get("device", "")) if data.get("device", "") else player.print_json("error", {"message": "No audio device provided."}),
        'fullscreen': lambda: player.set_fullscreen(data['fullscreen']),
        'repeat': lambda: handle_repeat(player, data),
        'hide_image': lambda: player.hide_image(),
        
        # logo and image handling
        'logo': lambda: player.set_logo(data.get('file', '').strip()),
        'show_logo': lambda: player.show_logo(data.get('show', False)),
        'logo_size': lambda: (
            player.pstatus.setdefault("logo", {}).update({"width": data.get('width', 0), "height": data.get('height', 0)}),
            player.show_logo(player.pstatus["logo"].get("show", False))
        ),
        # playlist commands
        'playlist': lambda: set_playlist(player, data.get("playlist", {}), data.get("playlistIndex", 0)),
        'playlist_track_index': lambda: set_playlist_index(player, data.get("index", 0)),
        'playlist_mode': lambda: set_playlist_mode(player, data.get("value", False)),
        'image_time': lambda: set_image_time(player, data),
        'next': lambda: player.handle_next_command(data.get("index")),
        # status
        'background_color': lambda: (player.set_background_color(data.get('color', '#ffffff')), player.pstatus.__setitem__('background', data.get('color', '#ffffff'))),
        'pstatus': lambda: update_pstatus(player, data),
    }

    func = dispatch.get(command)
    if func:
        func()
    else:
        player.print_json("error", {"message": f"Unknown command: {command}"})
