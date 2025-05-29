const {
  playid,
  play,
  pause,
  stop,
  updateTime,
  setFullscreen,
  setLogo,
  showLogo,
  setLogoSize,
  setBackground
} = require('@api/player')
const logger = require('@logger')
const parsing = (data) => {
  try {
    switch (data.type) {
      case 'playid':
        playid(data.value)
        break
      case 'play':
        sendMessageToPython(`play`)
        break
      case 'pause':
        sendMessageToPython('pause')
        break
      case 'stop':
        sendMessageToPython('stop')
        break
      case 'time':
        updateTime(data.value * 1000)
        break
      case 'fullscreen':
        setFullscreen(data.value)
        break
      case 'logo':
        setLogo(data.value)
        break
      case 'show_logo':
        showLogo(data.value)
        break
      case 'logo_size':
        setLogoSize(data.height, data.width)
        break
      case 'background':
        setBackground(data.value)
        break
      default:
        console.warn('Unknown data type:', data.type)
    }
  } catch (error) {
    logger.error('Error in parsing data:', error)
  }
}

module.exports = parsing
