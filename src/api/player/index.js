const path = require('path')
const logger = require('../../logger')
const { pStatus } = require('../../_status')
const { dbStatus, dbFiles } = require('../../db')
const { getLogoPath } = require('../files/folders')
const { setPlaylistMode } = require('../playlists')
const { sendPlayerCommand, sendMessageToClient } = require('..')
const { broadcastTcpMessage } = require('../../tcp')

const setMedia = async (id) => {
  logger.info(`Setting media with ID: ${id}`)
  const file = await dbFiles.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('File not found')
  }
  sendPlayerCommand('set_media', { file })
  setPlaylistMode(false)
  require('../../tcp').broadcastTcpMessage(`set,${id},${file.filename}`)
  return `Media set to: ${file.path}`
}

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)
  const file = await dbFiles.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }
  sendPlayerCommand('playid', { file: file })
  setPlaylistMode(false)
  require('../../tcp').broadcastTcpMessage(`playid,${id},${file.filename}`)

  return `Playing file: ${file.path}`
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
  require('../../tcp').broadcastTcpMessage('stop')
  return 'Player stopped'
}

const updateTime = (time, idx) => {
  sendPlayerCommand('set_time', { time, idx })
  require('../../tcp').broadcastTcpMessage(`set_time,${time}`)
  return `Time updated to: ${time} for player ${idx}`
}

const setFullscreen = async (value) => {
  sendPlayerCommand('set_fullscreen', { value })
  require('../../tcp').broadcastTcpMessage(`set_fullscreen,${value}`)
  return `Fullscreen mode set to: ${value}`
}

const setLogo = async (logo) => {
  const filePath = path.join(getLogoPath(), logo)

  pStatus.logo.file = filePath
  pStatus.logo.name = logo
  await dbStatus.update({ type: 'logo' }, { file: filePath, name: logo })
  sendMessageToClient('pStatus', {
    logo: pStatus.logo
  })
  sendPlayerCommand('logo_file', { file: filePath })
  logger.info(`Setting logo to: ${logo} at path: ${filePath}`)
  return `Logo set to: ${logo}`
}

const showLogo = async (show) => {
  pStatus.logo.show = show
  await dbStatus.update({ type: 'logo' }, { show })
  sendMessageToClient('pStatus', { logo: pStatus.logo })
  sendPlayerCommand('show_logo', { show })
  return `Logo visibility set to: ${show}`
}

const setLogoSize = async (size) => {
  logger.info(`Setting logo size to: ${size}`)
  pStatus.logo.size = size
  await dbStatus.update({ type: 'logo' }, { size })
  sendMessageToClient('pStatus', {
    logo: pStatus.logo
  })
  sendPlayerCommand('logo_size', {
    size
  })
  return `Logo size set to: ${size}`
}

const setBackground = async (background) => {
  if (!background || typeof background !== 'string') {
    logger.warn('Received invalid background color from Python')
    return
  }
  pStatus.background = background
  await dbStatus.update({ type: 'background' }, { color: background })
  sendMessageToClient('pStatus', {
    background: pStatus.background
  })
  sendPlayerCommand('background_color', { color: background })
  return `Background set to: ${background}`
}

const getAudioDevices = () => {
  sendPlayerCommand('get_audio_devices', {})
  return 'Requesting current audio device'
}

const setAudioDevice = async (deviceId) => {
  if (!deviceId) {
    logger.warn('Received invalid audiodevice message from Python')
    return
  }
  pStatus.device.audiodevice = deviceId
  await dbStatus.update({ type: 'audiodevice' }, { audiodevice: deviceId })
  sendMessageToClient('pStatus', {
    device: pStatus.device
  })
  sendPlayerCommand('set_audio_device', { device: deviceId })
  logger.info(`Setting audio device to: ${deviceId}`)
  return `Audio device set to: ${deviceId}`
}

const setImageTime = async (time) => {
  logger.info(`Setting image time to: ${time}`)
  sendPlayerCommand('image_time', { time })
  await dbStatus.update({ type: 'image_time' }, { time })
  sendMessageToClient('pStatus', {
    imageTime: time
  })
  return `Image time set to: ${time}`
}

const setRepeat = async (mode = null) => {
  let modes = ['none', 'all', 'repeat_one']
  if (pStatus.playlistMode === false) {
    modes = ['none', 'all']
  }
  if (mode && modes.includes(mode)) {
    pStatus.repeat = mode
  } else {
    const currentIdx = modes.indexOf(pStatus.repeat)
    pStatus.repeat = modes[(currentIdx + 1) % modes.length]
  }
  await dbStatus.update({ type: 'repeat' }, { mode: pStatus.repeat })
  logger.info(`Repeat mode set to: ${pStatus.repeat}`)
  sendMessageToClient('pStatus', {
    repeat: pStatus.repeat
  })
  return pStatus.repeat
}

const setNext = async () => {
  logger.info('Setting next track in playlist')
  sendPlayerCommand('next', {})
  require('../../tcp').broadcastTcpMessage(
    `next,${pStatus.playlist.playlistId},${pStatus.playlistTrackIndex + 1}`
  )
  return 'Next track set'
}

const setPrevious = async () => {
  logger.info('Setting previous track in playlist')
  sendPlayerCommand('previous', {})
  // 재생시간이 5초 미만이면 playlistTrackIndex를 -1
  if (pStatus.player[pStatus.activePlayerId].time < 5000) {
    require('../../tcp').broadcastTcpMessage(
      `previous,${pStatus.playlist.playlistId},${pStatus.playlistTrackIndex - 1}`
    )
  } else {
    require('../../tcp').broadcastTcpMessage(
      `previous,${pStatus.playlist.playlistId},${pStatus.playlistTrackIndex}`
    )
  }

  return 'Previous track set'
}

module.exports = {
  sendPlayerCommand,
  setMedia,
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
  getAudioDevices,
  setAudioDevice,
  setImageTime,
  setRepeat,
  setNext,
  setPrevious
}
