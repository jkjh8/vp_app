const db = require('@db')
const logger = require('@logger')
const pStatus = require('@src/_status')

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)

  const file = await db.files.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }

  pStatus.current = file

  // sendMessageToPython(`play:${currentFile.path}`)
  require('@py').sendMessageToPython({ command: 'playid', file: file })

  return `Playing file: ${file.path}`
}

const play = () => {
  logger.info('Received play request without ID')
  require('@py').sendMessageToPython({ command: 'play' })
  return 'Playing without ID'
}

const pause = () => {
  logger.info('Received pause request')
  require('@py').sendMessageToPython({ command: 'pause' })
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  require('@py').sendMessageToPython({ command: 'stop' })
  return 'Player stopped'
}

const updateTime = (time) => {
  logger.info(`Updating player time to: ${time}`)
  require('@py').sendMessageToPython({ command: 'time', time })
}

const setFullscreen = (fullscreen) => {
  logger.info(`Setting fullscreen mode to: ${fullscreen}`)
  require('@py').sendMessageToPython({ command: 'fullscreen', fullscreen })
}

const setLogo = (logo) => {
  logger.info(`Setting logo to: ${logo}`)
  require('@py').sendMessageToPython({ command: 'logo', path: logo })
}

const showLogo = (show) => {
  logger.info(`Setting logo visibility to: ${show}`)
  require('@py').sendMessageToPython({ command: 'show_logo', value: show })
}

const setLogoSize = (h, w) => {
  logger.info(`Setting logo size to: height=${h}, width=${w}`)
  require('@py').sendMessageToPython({
    command: 'logo_size',
    height: h,
    width: w
  })
}

const setBackground = (background) => {
  logger.info(`Setting background to: ${background}`)
  require('@py').sendMessageToPython({
    command: 'background',
    color: background
  })
}

module.exports = {
  playid,
  play,
  stop,
  pause,
  updateTime,
  setFullscreen,
  setLogo,
  showLogo,
  setLogoSize,
  setBackground
}
