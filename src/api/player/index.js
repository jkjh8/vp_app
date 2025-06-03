const path = require('path')
const logger = require('@logger')
const { pStatus } = require('@src/_status')
const { dbStatus, dbFiles } = require('@db')
const { getLogoPath } = require('@api/files/folders')

const sendPlayerCommand = (command, data) => {
  logger.info(`Sending command to player: ${command}`, data)
  require('@py').send({ command, ...data })
}

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)
  const file = await dbFiles.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }
  pStatus.current = file
  pStatus.playlistMode = false
  sendPlayerCommand('playid', { file: file })
  return `Playing file: ${file.path}`
}

const play = () => {
  logger.info('Received play request without ID')
  sendPlayerCommand('play', {})
  return 'Playing without ID'
}

const pause = () => {
  logger.info('Received pause request')
  sendPlayerCommand('pause', {})
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  sendPlayerCommand('stop', {})
  return 'Player stopped'
}

const updateTime = (time) => {
  logger.info(`Updating player time to: ${time}`)
  sendPlayerCommand('time', { time })
}

const setFullscreen = async (fullscreen) => {
  sendPlayerCommand('fullscreen', { fullscreen })
  return `Fullscreen mode set to: ${fullscreen}`
}

const setLogo = async (logo) => {
  logger.info(`Setting logo to: ${logo}`)
  const filePath = path.join(getLogoPath(), logo)

  pStatus.logo.name = logo
  pStatus.logo.file = filePath
  await dbStatus.update(
    { type: 'logo' },
    { $set: { file: filePath, name: logo } },
    { upsert: true }
  )
  sendPlayerCommand('logo', { file: filePath })
  return `Logo set to: ${logo}`
}

const showLogo = async (show) => {
  logger.info(`Setting logo visibility to: ${show}`)
  pStatus.logo.show = show
  await dbStatus.update({ type: 'logo' }, { $set: { show } }, { upsert: true })
  sendPlayerCommand('show_logo', { show })
  return `Logo visibility set to: ${show}`
}

const setLogoSize = async (h, w) => {
  logger.info(`Setting logo size to: height=${h}, width=${w}`)
  pStatus.logo.height = h
  pStatus.logo.width = w
  await dbStatus.update(
    { type: 'logo' },
    { $set: { height: h, width: w } },
    { upsert: true }
  )
  sendPlayerCommand('logo_size', {
    height: h,
    width: w
  })
  return `Logo size set to: height=${h}, width=${w}`
}

const setBackground = async (background) => {
  sendPlayerCommand('background_color', { color: background })
  return `Background set to: ${background}`
}

const setAudioDevice = async (deviceId) => {
  logger.info(`Setting audio device to: ${deviceId}`)
  sendPlayerCommand('set_audio_device', { device: deviceId })
  return `Audio device set to: ${deviceId}`
}

const setImageTime = async (time) => {
  logger.info(`Setting image time to: ${time}`)
  sendPlayerCommand('image_time', { time })
  return `Image time set to: ${time}`
}

module.exports = {
  sendPlayerCommand,
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
  setAudioDevice,
  setImageTime
}
