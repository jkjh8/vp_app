let { pStatus } = require('@src/_status.js')
const logger = require('@logger')
const { dbStatus } = require('@db')
const { sendMessageToClient } = require('@web/io')
const { sendPlayerCommand } = require('@api/player')
const db = require('../../db')
const { log } = require('electron-builder')

function handleInfoMessage(data) {
  pStatus = { ...pStatus, ...data }
  sendMessageToClient('pStatus', pStatus)
}

function handleLogMessage(level, prefix, data) {
  const message =
    prefix +
    (typeof data === 'object' && data !== null ? JSON.stringify(data) : data)
  if (level === 'error') {
    logger.error(message)
  } else if (level === 'warn') {
    logger.warn(message)
  } else {
    logger.info(message)
  }
}

function handleEndReached(data) {
  pStatus.playlistIndex = data.playlist_index ?? 0
  switch (pStatus.repeat) {
    case 'none':
      if (pStatus.playlistMode) {
        if (
          pStatus.playlist.length > 0 &&
          data.data.playlist_index < pStatus.playlist.length - 1
        ) {
          logger.info(
            `End of track reached(none), moving to next track in playlist. Current index: ${data.data.playlist_index}`
          )
          sendPlayerCommand({ command: 'next' })
        } else {
          sendPlayerCommand({ command: 'stop' })
        }
      } else {
        logger.info('End of track reached, stopping playback.')
        sendPlayerCommand({ command: 'stop' })
      }
      break
    case 'all':
      if (pStatus.playlistMode) {
        logger.info('End of playlist reached, stopping playback.')
        sendPlayerCommand({ command: 'next' })
      } else {
        logger.info('End of track reached, stopping playback.')
        sendPlayerCommand({ command: 'stop' })
        sendPlayerCommand({ command: 'play' })
      }
      break
    case 'single':
      logger.info('End of single track reached, stopping playback.')
      sendPlayerCommand({ command: 'stop' })
      break
    case 'repeat_one':
      logger.info('Repeat one mode, restarting current track.')
      sendPlayerCommand({ command: 'stop' })
      sendPlayerCommand({ command: 'play' })
      break
  }
}

function handleMediaChanged(data) {
  if (!data || typeof data.playlist_index === 'undefined') {
    logger.warn('Received invalid media_changed message from Python')
    return
  }

  pStatus.playlistIndex = data.playlist_index

  if (pStatus.playlistMode && pStatus.playlistIndex >= 0) {
    logger.info(
      `Media changed, updating current track index to ${pStatus.playlistIndex}`
    )
    pStatus.current = pStatus.playlist[pStatus.playlistIndex]
  } else {
    logger.info('Media changed, resetting current track index.')
    pStatus.current = null
  }

  sendMessageToClient('pStatus', {
    current: pStatus.current,
    playlistIndex: pStatus.playlistIndex
  })
}

const parsing = async (data) => {
  const lines = data.toString('utf8').split('\n').filter(Boolean)
  for (const line of lines) {
    try {
      const { type, data } = JSON.parse(line)
      switch (type) {
        case 'info':
          handleInfoMessage(data)
          break
        case 'stop':
          logger.info(`Received stop command from Python:${data}`)
          sendPlayerCommand({ command: 'stop' })
          break
        case 'end_reached':
          handleEndReached(data)
          break
        case 'player_data':
          pStatus.player = { ...pStatus.player, ...data }
          sendMessageToClient('pStatus', { player: data })
          break
        case 'audiodevices':
          pStatus.device.audiodevices = data.devices
          sendMessageToClient('pStatus', {
            device: { audiodevices: data.devices }
          })
          break
        case 'audiodevice':
          if (!data || !data.device) {
            logger.warn('Received invalid audiodevice message from Python')
            break
          }
          pStatus.device.audiodevice = data.device
          await dbStatus.update(
            { type: 'audiodevice' },
            { $set: { audiodevice: data.device } },
            { upsert: true }
          )
          sendMessageToClient('pStatus', {
            device: { audiodevice: data.device }
          })
          logger.info(`Python Audio device changed to ${data.device}`)
          break
        case 'media_changed':
          handleMediaChanged(data)
          break
        case 'set_image_time':
          pStatus.imageTime = data.image_time
          sendMessageToClient('pStatus', { imageTime: data.image_time })
          await db.dbStatus.update(
            { type: 'image_time' },
            { $set: { time: data.image_time } },
            { upsert: true }
          )
          break
        case 'set_background':
          pStatus.background = data.background
          sendMessageToClient('pStatus', { background: data.background })
          await dbStatus.update(
            { type: 'background' },
            { $set: { value: data.background } },
            { upsert: true }
          )
          logger.info(`Background color set to ${data.background}`)
          break
        case 'set_fullscreen':
          pStatus.player.fullscreen = data.fullscreen
          sendMessageToClient('pStatus', {
            player: { fullscreen: data.fullscreen }
          })
          await dbStatus.update(
            { type: 'fullscreen' },
            { $set: { fullscreen: data.fullscreen } },
            { upsert: true }
          )
          logger.info(`Fullscreen mode set to ${data.fullscreen}`)
          break
        case 'message':
          handleLogMessage('info', 'Received message from Python:', data)
          break
        case 'error':
          handleLogMessage('error', 'Received error from Python:', data)
          break
        default:
          handleLogMessage(
            'warn',
            'Received unknown message type from Python: ',
            { type, data }
          )
          break
      }
    } catch (error) {
      logger.error(`Error parsing JSON from Python:${error} Original:${line}`)
    }
  }
}

module.exports = {
  parsing
}
