let { pStatus } = require('@src/_status.js')
const logger = require('@logger')
const { dbStatus, dbFiles } = require('@db')
const { sendMessageToClient, sendPlayerCommand } = require('@api')

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
  pStatus.playlistTrackIndex = data.playlist_index ?? 0
  const idx = data.id ?? 0
  switch (pStatus.repeat) {
    case 'none':
      if (pStatus.playlistMode) {
        if (
          pStatus.playlist.length > 0 &&
          data.playlist_index < pStatus.playlist.length - 1
        ) {
          logger.info(
            `End of track reached(none), moving to next track in playlist. Current index: ${data.playlist_index}`
          )
          sendPlayerCommand('next', {})
        } else {
          sendPlayerCommand('stop', { idx })
        }
      } else {
        logger.info('End of track reached, stopping playback.')
        sendPlayerCommand('stop', { idx })
      }
      break
    case 'all':
      if (pStatus.playlistMode) {
        logger.info('End of playlist reached, stopping playback.')
        sendPlayerCommand('next', {})
      } else {
        logger.info('End of track reached, stopping playback.')
        sendPlayerCommand('stop', { idx })
        sendPlayerCommand('next', {})
      }
      break
    case 'single':
      logger.info('End of single track reached, stopping playback.')
      sendPlayerCommand('stop', { idx })
      break
    case 'repeat_one':
      logger.info('Repeat one mode, restarting current track.')
      sendPlayerCommand('stop', { idx })
      sendPlayerCommand('play', { idx })
      break
  }
}

async function handleMediaChanged(data) {
  logger.info(`Media changed event received: ${JSON.stringify(data)}`)
  if (data.uuid) {
    const file = await dbFiles.findOne({ uuid: data.uuid })
    pStatus.player[data.idx] = { ...pStatus.player[data.idx], file: file }
    logger.info(
      `Media changed for player ${data.idx}, file: ${file.filename}, uuid: ${file.uuid}`
    )
  }
  if (data.playlist_track_index) {
    pStatus.playlistTrackIndex = data.playlist_track_index
    pStatus.player[data.idx] = {
      ...pStatus.player[data.idx],
      file: pStatus.tracks[pStatus.playlistTrackIndex]
    }
    logger.info(
      `Media changed, current track set to index ${pStatus.playlistTrackIndex}, file: ${pStatus.player[data.idx].file.filename}`
    )
  }

  sendMessageToClient('pStatus', {
    player: pStatus.player,
    playerTrackIndex: pStatus.playlistTrackIndex
  })
}

const parsing = async (data) => {
  const lines = data.toString('utf8').split('\n').filter(Boolean)
  for (const line of lines) {
    try {
      const { type, data } = JSON.parse(line)
      switch (type) {
        case 'info':
          logger.info('Received info message from Python:' + data)
          break
        case 'debug':
          logger.debug('Received debug message from Python:' + data)
          break
        case 'message':
          handleLogMessage('info', 'Received message from Python:', data)
          break
        case 'error':
          handleLogMessage('error', 'Received error from Python:', data)
          break
        case 'active_player_id':
          pStatus.active_player_id = data.id
          sendMessageToClient('pStatus', { activePlayerId: data.id })
          break
        case 'stop':
          logger.info(`Received stop command from Python:${data}`)
          sendPlayerCommand('stop', {})
          break
        case 'player_data':
          pStatus.player[data.id] = { ...pStatus.player[data.id], ...data }
          sendMessageToClient('pStatus', { player: pStatus.player })
          break
        case 'media_changed':
          handleMediaChanged(data)
          break
        case 'end_reached':
          handleEndReached(data)
          break
        case 'audiodevices':
          pStatus.device.audiodevices = data.devices
          logger.debug(
            `Received audio devices from Python: ${JSON.stringify(data.devices)}`
          )
          // Update the audio devices in pStatus
          sendMessageToClient('pStatus', {
            device: { audiodevices: data.devices }
          })
          break
        case 'set_image_time':
          pStatus.image_time = data.image_time
          sendMessageToClient('pStatus', { image_time: data.image_time })
          await dbStatus.update(
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

        case 'playlist_set':
          pStatus.playlist = data.playlist || []
          pStatus.playlistTrackIndex = data.playlist_index || 0
          sendMessageToClient('pStatus', {
            playlist: pStatus.playlist,
            playlistTrackIndex: pStatus.playlistTrackIndex
          })
          await dbStatus.update(
            { type: 'playlist' },
            {
              $set: {
                playlist: pStatus.playlist,
                playlistTrackIndex: pStatus.playlistTrackIndex
              }
            },
            { upsert: true }
          )
          logger.info(
            `Playlist set with ${pStatus.playlist.length} tracks, current index: ${pStatus.playlistTrackIndex}`
          )
          break
        case 'playlist_index_set':
          pStatus.playlistTrackIndex = data.index || 0
          sendMessageToClient('pStatus', {
            playlistTrackIndex: pStatus.playlistTrackIndex
          })
          await dbStatus.update(
            { type: 'playlistTrackIndex' },
            { $set: { playlistTrackIndex: pStatus.playlistTrackIndex } },
            { upsert: true }
          )
          logger.info(`Playlist index set to ${pStatus.playlistTrackIndex}`)
          break
        case 'playlist_mode':
          pStatus.playlistMode = data.mode || false
          sendMessageToClient('pStatus', { playlistMode: pStatus.playlistMode })
          await dbStatus.update(
            { type: 'playlistMode' },
            { $set: { value: pStatus.playlistMode } },
            { upsert: true }
          )
          logger.info(`Playlist mode set to ${pStatus.playlistMode}`)
          break
        case 'current_track':
          console.log('Received current_track message from Python:', data)
          const uuid = data.uuid || null
          if (uuid) {
            const file = await dbFiles.findOne({ uuid })
            if (file) {
              pStatus.current = file
              sendMessageToClient('pStatus', { current: file })
            }
          }
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
