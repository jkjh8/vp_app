const player = require('@api/player')
const playlists = require('@api/playlists')

async function handleMessage(msg) {
  try {
    const [command, ...params] = msg.toString().trim().split(',')
    let r = 'OK'
    switch (command) {
      case 'playid':
        player.playid(Number(params[0]))
        break
      case 'play':
        player.play(Number(params[0]))
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
        player.setFullscreen(params[0] === 'true')
        break
      case 'logo':
        player.setLogo(params[0])
        break
      case 'show_logo':
        player.showLogo(params[0] === 'true')
        break
      case 'logo_size':
        player.setLogoSize(Number(params[0]))
        break
      case 'background':
        player.setBackground(params[0])
        break
      case 'playlist':
        const rt = await playlists.playlistPlay(
          Number(params[0]),
          Number(params[1] ?? 0)
        )
        if (rt) {
          r = rt
        }
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
