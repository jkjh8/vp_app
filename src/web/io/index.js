const {
  playid,
  updateTime,
  setFullscreen,
  setLogo,
  showLogo,
  setLogoSize,
  setBackground,
  sendPlayerCommand
} = require('@api/player')
const logger = require('@logger')
let { pStatus } = require('@/_status')

const parsing = (data) => {
  try {
    switch (data.type) {
      case 'playid':
        playid(data.value)
        break
      case 'play':
        sendPlayerCommand('play', { idx: data.idx })
        break
      case 'pause':
        sendPlayerCommand('pause', { idx: data.idx })
        break
      case 'stop':
        sendPlayerCommand('stop', {})
        break
      case 'time':
        updateTime(data.value * 1000, data.idx)
        break
      case 'fullscreen':
        setFullscreen(data.value)
        break
      case 'logo':
        setLogo(data.value)
        pStatus.logo.file = data.value
        pStatus.logo.show = true
        break
      case 'show_logo':
        showLogo(data.value)
        pStatus.logo.show = data.value
        break
      case 'logo_size':
        setLogoSize(data.height, data.width)
        pStatus.logo.height = data.height
        pStatus.logo.width = data.width
        break
      case 'background':
        setBackground(data.value)
        pStatus.background = data.value
        break
      default:
        logger.warn('Unknown data type:', data.type)
    }
  } catch (error) {
    logger.error('Error in parsing data:', error)
  }
}

module.exports = { parsing }
