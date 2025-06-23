const player = require('../player')
const playlists = require('../playlists')
const { dbPlaylists } = require('../../db')

async function handleMessage(msg) {
  try {
    const [command, ...params] = msg.toString().trim().split(',')
    let r = 'OK'
    switch (command) {
      case 'playid':
        player.playid(Number(params[0]))
        break
      case 'play_file':
        const file = params[0]
        if (!file) {
          throw new Error('File parameter is required')
        }
        await player.play_file(file)
        break
      case 'play':
        player.play()
        break
      case 'stop':
        player.stop()
        break
      case 'pause':
        player.pause(Number(params[0]))
        break
      case 'time':
        player.updateTime(Number(params[0]) * 1000, Number(params[1]))
        break
      case 'fullscreen':
        player.setFullscreen(params[0] === 'true' || params[0] === '1')
        break
      case 'logo':
        player.setLogo(params[0])
        break
      case 'show_logo':
        player.showLogo(params[0] === 'true' || params[0] === '1')
        break
      case 'logo_size':
        player.setLogoSize(Number(params[0]))
        break
      case 'background':
        player.setBackground(params[0])
        break
      case 'playlist_get':
        const tracks = await playlists.getPlaylist(Number(params[0]))
        if (tracks) {
          r = `playlist_get,${tracks.map((t) => t.filename).join(',')}`
        }
        break
      case 'playlist_play':
        const rt = await playlists.playlistPlay(
          Number(params[0]),
          Number(params[1] ?? 0)
        )
        if (rt) {
          r = rt
        }
        break
      case 'playlist_get_json':
        const playlist = await playlists.getPlaylist(Number(params[0]))
        if (playlist) {
          r = `playlist_get_json,${JSON.stringify(playlist)}`
        }
        break
      case 'playlist_amx':
        const playlistAmx = await dbPlaylists.findOne({
          playlistId: Number(params[0])
        })
        if (playlistAmx) {
          r = `playlist_amx,${playlistAmx.tracks.map((t) => t.amx).join(',')}`
        }
        break
      case 'next':
        player.setNext()
        break
      case 'prev':
        player.setPrevious()
        break
      default:
        r = `Unknown command: ${command}`
        break
    }
    return r
  } catch (error) {
    return error
  }
}

module.exports = { handleMessage }
