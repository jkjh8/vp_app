const { sendMessageToPython } = require('@py')
const db = require('@db')
const logger = require('@logger')

let currentFile = null

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)

  if (!id) {
    sendMessageToPython('play')
    return 'Playing without ID'
  }

  currentFile = await db.files.findOne({ number: Number(id) })
  if (!currentFile) {
    throw new Error('Player not found')
  }

  const { io } = require('@web/io')

  io.emit('current', currentFile)

  // sendMessageToPython(`play:${currentFile.path}`)
  sendMessageToPython({ command: 'playid', file: currentFile })

  return `Playing file: ${currentFile.path}`
}

const play = () => {
  logger.info('Received play request without ID')
  sendMessageToPython({ command: 'play' })
  return 'Playing without ID'
}

const pause = () => {
  logger.info('Received pause request')
  sendMessageToPython({ command: 'pause' })
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  sendMessageToPython({ command: 'stop' })
  return 'Player stopped'
}

const updateTime = (time) => {
  logger.info(`Updating player time to: ${time}`)
  sendMessageToPython({ command: 'time', time })
}

const setFullscreen = (fullscreen) => {
  logger.info(`Setting fullscreen mode to: ${fullscreen}`)
  sendMessageToPython({ command: 'fullscreen', fullscreen })
}

const setLogo = (logo) => {
  logger.info(`Setting logo to: ${logo}`)
  sendMessageToPython({ command: 'logo', path: logo })
}

const showLogo = (show) => {
  logger.info(`Setting logo visibility to: ${show}`)
  sendMessageToPython({ command: 'show_logo', value: show })
}

const setLogoSize = (h, w) => {
  logger.info(`Setting logo size to: height=${h}, width=${w}`)
  sendMessageToPython({ command: 'logo_size', height: h, width: w })
}

const setBackground = (background) => {
  logger.info(`Setting background to: ${background}`)
  sendMessageToPython({ command: 'background', color: background })
}

const sendPlayerData = (data) => {
  socket.io.emit('player', data)
}

const sendCurrentFile = () => {
  if (currentFile) {
    const { io } = require('@web/io')
    io.emit('current', currentFile)
  } else {
    logger.warn('No current file to send')
  }
}

module.exports = {
  currentFile: () => currentFile,
  playid,
  play,
  stop,
  pause,
  updateTime,
  setFullscreen,
  setLogo,
  showLogo,
  setLogoSize,
  setBackground,
  sendPlayerData,
  sendCurrentFile
}
