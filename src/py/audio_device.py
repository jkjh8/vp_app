import os
import vlc


def initDoublePlayers(player):
    # VLC 인스턴스 2개 생성
    player.instanceA = vlc.Instance(
        "--no-video-title-show",
        "--avcodec-hw=any",
        "--no-drop-late-frames",
        "--no-skip-frames"
    )
    player.instanceB = vlc.Instance(
        "--no-video-title-show",
        "--avcodec-hw=any",
        "--no-drop-late-frames",
        "--no-skip-frames"
    )
    player.playerA = player.instanceA.media_player_new()
    player.playerB = player.instanceB.media_player_new()
    player.playerA.set_hwnd(int(player.winId()))
    player.playerB.set_hwnd(int(player.winId()))
    player.active_player = player.playerA
    player.next_player = player.playerB
    # 이벤트 핸들러 등록
    init_events_double(player)
    # 오디오 디바이스 가져오기 및 설정
    get_audio_devices(player)
    
def init_events_double(player):
    try:
        event_types = [
            (vlc.EventType.MediaPlayerEndReached, lambda event: on_end_reached(player, event)),
            (vlc.EventType.MediaPlayerEncounteredError, lambda event: on_error(player, event)),
            (vlc.EventType.MediaPlayerTimeChanged, lambda event: update_player_data(player, event)),
            (vlc.EventType.MediaPlayerPlaying, lambda event: update_player_data(player, event)),
            (vlc.EventType.MediaPlayerPaused, lambda event: update_player_data(player, event)),
            (vlc.EventType.MediaPlayerStopped, lambda event: update_player_data(player, event)),
            (vlc.EventType.MediaPlayerMediaChanged, lambda event: update_player_data(player, event)),
        ]
        for which_player in [player.playerA, player.playerB]:
            em = which_player.event_manager()
            for event_type, handler in event_types:
                em.event_attach(event_type, _make_event_handler(player, handler, which_player))
    except Exception as e:
        player.print_json("error", {"message": f"Error initializing double player events: {e}"})

def _make_event_handler(player, handler, which_player):
        def event_handler(event):
            event._which_player = which_player
            handler(event)
        return event_handler

def on_error(player, event):
        player.print_json("error", {"message": "Error occurred"})

def on_end_reached(player, event):
        try:
            update_player_data(player, event)
            # Notify Node.js that playback has ended; Node.js will handle next action
            player.print_json("event", {"event": "end_reached", "playlist_index": player.pstatus['playlistindex']})
        except Exception as e:
            player.print_json("error", {"message": f"Exception in on_end_reached: {e}"})

def get_audio_devices(player):
    """
    VLC에서 사용 가능한 오디오 디바이스 목록을 반환합니다.
    """
    try:
        devices = []
        if not player.playerA:
            player.print_json("error", {"message": "VLC player not initialized."})
            return
        dev_list = player.playerA.audio_output_device_enum()
        if dev_list:
            dev = dev_list
            while dev:
                dev_info = dev.contents
                devices.append({
                    "deviceid": dev_info.device.decode() if dev_info.device else "default",
                    "name": dev_info.description.decode() if dev_info.description else "기본 장치"
                })
                dev = dev_info.next
        player.pstatus.setdefault('device', {})
        player.pstatus['device']['audiodevices'] = devices
        player.pstatus['device']['audiodevice'] = player.playerA.audio_output_device_get() or "default"
        player.print_json("info", player.pstatus)
    except Exception as e:
        player.print_json("error", {"message": f"Error getting audio devices: {e}"})


def set_audio_device(player, device):
    """
    지정된 오디오 디바이스로 모든 플레이어를 설정합니다.
    :param device: str, 오디오 디바이스 이름
    """
    try:
        if not device or device == "":
            player.print_json("error", {"message": "No audio device provided."})
            return
        # 모든 플레이어에 오디오 디바이스 설정
        if hasattr(player, 'playerA') and player.playerA:
            player.playerA.audio_output_device_set(device)
        if hasattr(player, 'playerB') and player.playerB:
            player.playerB.audio_output_device_set(device)
        # 현재 오디오 디바이스 확인
        current_device = player.active_player.audio_output_device_get()
        if current_device == device:
            player.pstatus['device']['audiodevice'] = current_device
            player.print_json("info", player.pstatus)
        else:
            player.print_json("error", {"message": f"Failed to set audio device to {device}."})
    except Exception as e:
        player.print_json("error", {"message": f"Error setting audio device: {e}"})


def update_player_data(player, event=None):
        # 이벤트가 있으면 어떤 플레이어에서 발생했는지 확인
        active_player = getattr(event, "_which_player", None) if event is not None else player.active_player
        # 현재 활성 플레이어만 처리
        if active_player != player.active_player:
            return
        event_type = getattr(event, "type", "manual") if event is not None else "manual"
        player.pstatus.setdefault('player', {})
        player.pstatus['player']['event'] = str(event_type)
        media = player.active_player.get_media()
        if media is not None:
            player.pstatus['player']['filename'] = media.get_mrl()
        else:
            player.pstatus['player']['filename'] = ""
        player.pstatus['player']['duration'] = player.active_player.get_length()
        player.pstatus['player']['time'] = player.active_player.get_time()
        player.pstatus['player']['position'] = player.active_player.get_position()
        player.pstatus['player']['playing'] = player.active_player.is_playing()
        player.pstatus['player']['volume'] = player.active_player.audio_get_volume()
        player.pstatus['player']['speed'] = player.active_player.get_rate()
        player.pstatus['player']['fullscreen'] = player.active_player.get_fullscreen()
        player.print_json("info", player.pstatus)