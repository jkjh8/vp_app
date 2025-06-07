const path = require('path')
const logger = require('@logger')
const { pStatus } = require('@src/_status')
const { dbStatus, dbFiles } = require('@db')
const { getLogoPath } = require('@api/files/folders')
const { setPlaylistMode } = require('@api/playlists')
const { sendPlayerCommand, sendMessageToClient } = require('@api')

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)
  const file = await dbFiles.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }
  pStatus.current = file
  sendPlayerCommand('playid', { file: file })
  setPlaylistMode(false)
  return `Playing file: ${file.path}`
}

const playlistPlay = async (playlistId, trackIndex) => {
  // playlistId와 trackIndex가 유효한지 확인
}

const play = (idx) => {
  logger.info('Received play request without ID')
  sendPlayerCommand('play', { idx })
  return 'Playing without ID'
}

const pause = (idx) => {
  logger.info('Received pause request')
  sendPlayerCommand('pause', { idx })
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  sendPlayerCommand('stop_all', {})
  return 'Player stopped'
}

const updateTime = (time, idx) => {
  logger.info(`Updating player time to: ${time} for index: ${idx}`)
  sendPlayerCommand('set_time', { time, idx })
}

const setFullscreen = async (value) => {
  sendPlayerCommand('set_fullscreen', { value })
  return `Fullscreen mode set to: ${value}`
}

const setLogo = async (logo) => {
  const filePath = path.join(getLogoPath(), logo)
  pStatus.logo.file = filePath
  pStatus.logo.name = logo
  await dbStatus.update(
    { type: 'logo' },
    { $set: { file: filePath, name: logo } },
    { upsert: true }
  )
  sendMessageToClient('pStatus', {
    logo: pStatus.logo
  })
  sendPlayerCommand('logo_file', { file: filePath })
  logger.info(`Setting logo to: ${logo} at path: ${filePath}`)
  return `Logo set to: ${logo}`
}

const showLogo = async (show) => {
  logger.info(`Setting logo visibility to: ${show}`)
  pStatus.logo.show = show
  await dbStatus.update({ type: 'logo' }, { $set: { show } }, { upsert: true })
  sendMessageToClient('pStatus', { logo: pStatus.logo })
  sendPlayerCommand('show_logo', { show })
  return `Logo visibility set to: ${show}`
}

const setLogoSize = async (size) => {
  logger.info(`Setting logo size to: ${size}`)
  pStatus.logo.size = size
  await dbStatus.update({ type: 'logo' }, { $set: { size } }, { upsert: true })
  sendMessageToClient('pStatus', {
    logo: pStatus.logo
  })
  sendPlayerCommand('logo_size', {
    size
  })
  return `Logo size set to: ${size}`
}

const setBackground = async (background) => {
  sendPlayerCommand('background_color', { color: background })
  return `Background set to: ${background}`
}

const setAudioDevice = async (deviceId) => {
  if (!deviceId) {
    logger.warn('Received invalid audiodevice message from Python')
    return
  }
  pStatus.device.audiodevice = deviceId
  await dbStatus.update(
    { type: 'audiodevice' },
    { $set: { audiodevice: deviceId } },
    { upsert: true }
  )
  sendMessageToClient('pStatus', {
    device: pStatus.device
  })
  sendPlayerCommand('set_audio_device', { device: deviceId })
  logger.info(`Setting audio device to: ${deviceId}`)
  return `Audio device set to: ${deviceId}`
}

const setImageTime = async (time, idx) => {
  logger.info(`Setting image time to: ${time} for index: ${idx}`)
  sendPlayerCommand('image_time', { time, idx })
  return `Image time set to: ${time} for index: ${idx}`
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
