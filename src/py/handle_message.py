import json
import os
from audio_device import get_audio_devices, set_audio_device

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
        'set': lambda: handle_set(player, data),
        'playid': lambda: handle_playid(player, data),
        'play': lambda: player.show_image(player.pstatus['current'].get("path", "")) if player.pstatus['current'].get("is_image", True) else player.active_player.play(),
        'stop': lambda: player.hide_image() if player.pstatus['current'].get("is_image", True) else player.active_player.stop(),
        'pause': lambda: player.active_player.pause(),
        'resume': lambda: player.active_player.play() if not player.pstatus['current'].get("is_image", True) else None,
        'hide_image': lambda: player.hide_image(),
        'volume': lambda: player.active_player.audio_set_volume(data['volume']),
        'position': lambda: player.active_player.set_position(data['position']),
        'time': lambda: player.active_player.set_time(data['time']),
        'speed': lambda: player.active_player.set_rate(data['speed']),
        'fullscreen': lambda: player.set_fullscreen(data['fullscreen']),
        'background_color': lambda: (player.set_background_color(data['color']), player.pstatus.__setitem__('background', data['color'])),
        'logo': lambda: (
            player.set_logo(data.get('file', '').strip()),
        ),
        'show_logo': lambda: (player.show_logo(data['show'])),
        'logo_size': lambda: (
            player.pstatus.setdefault("logo", {}).update({"width": data['width'], "height": data['height']}),
            player.show_logo(player.pstatus["logo"].get("show", False))
        ),
        'get_audio_devices': lambda: get_audio_devices(player),
        'set_audio_device': lambda: set_audio_device(player, data.get("device", "")) if data.get("device", "") else player.print_json("error", {"message": "No audio device provided."}),
        'initialize': lambda: (player.update_pstatus_except_player(data.get("pstatus", {})), player.initUi()) if isinstance(data.get("pstatus", {}), dict) else player.print_json("error", {"message": "Invalid pstatus format. Expected a JSON object."}),
        'pstatus': lambda: update_pstatus(player, data),
        'playlist': lambda: player.set_playlist(data.get("playlist", []), data.get("index", 0)),
        'next': lambda: player.handle_next_command(data.get("index")),
        'repeat': lambda: handle_repeat(player, data),
        'get_devices': lambda: get_audio_devices(player),
        'set_device': lambda: set_audio_device(player, data.get("device", "")) if data.get("device", "") else player.print_json("error", {"message": "No audio device provided."}),
    }

    func = dispatch.get(command)
    if func:
        func()
    else:
        player.print_json("error", {"message": f"Unknown command: {command}"})
