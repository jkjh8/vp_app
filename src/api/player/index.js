const db = require('@db')
const logger = require('@logger')
const pStatus = require('@src/_status')
const { dbStatus, dbFiles } = require('@db')

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)

  const file = await dbFiles.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }

  pStatus.current = file

  // send(`play:${currentFile.path}`)
  require('@py').send({ command: 'playid', file: file })

  return `Playing file: ${file.path}`
}

const play = () => {
  logger.info('Received play request without ID')
  require('@py').send({ command: 'play' })
  return 'Playing without ID'
}

const pause = () => {
  logger.info('Received pause request')
  require('@py').send({ command: 'pause' })
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  require('@py').send({ command: 'stop' })
  return 'Player stopped'
}

const updateTime = (time) => {
  logger.info(`Updating player time to: ${time}`)
  require('@py').send({ command: 'time', time })
}

const setFullscreen = (fullscreen) => {
  logger.info(`Setting fullscreen mode to: ${fullscreen}`)
  require('@py').send({ command: 'fullscreen', fullscreen })
}

const setLogo = (logo) => {
  logger.info(`Setting logo to: ${logo}`)
  require('@py').send({ command: 'logo', path: logo })
}

const showLogo = (show) => {
  logger.info(`Setting logo visibility to: ${show}`)
  require('@py').send({ command: 'show_logo', value: show })
}

const setLogoSize = (h, w) => {
  logger.info(`Setting logo size to: height=${h}, width=${w}`)
  require('@py').send({
    command: 'logo_size',
    height: h,
    width: w
  })
}

const setBackground = (background) => {
  logger.info(`Setting background to: ${background}`)
  require('@py').send({
    command: 'background',
    color: background
  })
}

const setImageTime = (time) => {
  logger.info(`Setting image time to: ${time}`)
  require('@py').send({
    command: 'image_time',
    time
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
  setBackground,
  setImageTime
}
