let { pStatus } = require('../../_status.js')
const logger = require('../../logger')
const { dbStatus, dbFiles } = require('../../db')
const { sendMessageToClient, sendPlayerCommand } = require('../../api')
const { broadcastTcpMessage } = require('../../tcp')
let lastEndReachedEvent = null

function handleEndReached(data) {
  const eventKey = `${data.playlist_track_index}-${data.active_player_id}`
  if (lastEndReachedEvent === eventKey) {
    logger.warn(`Duplicate end_reached event ignored: ${eventKey}`)
    return
  }
  lastEndReachedEvent = eventKey

  logger.info(`End reached event received: ${JSON.stringify(data)}`)
  pStatus.playlistTrackIndex = data.playlist_track_index
  pStatus.activePlayerId = data.active_player_id
  sendMessageToClient('pStatus', {
    playlistTrackIndex: pStatus.playlistTrackIndex,
    activePlayerId: pStatus.activePlayerId
  })

  const isLastTrack = pStatus.playlistTrackIndex === pStatus.tracks.length - 1
  const playerId = pStatus.activePlayerId

  switch (pStatus.repeat) {
    case 'none':
      if (pStatus.playlistMode) {
        if (!isLastTrack) {
          logger.info(
            `End of track reached (none), moving to next track. Index: ${pStatus.playlistTrackIndex}/${pStatus.tracks.length}`
          )
          if (lastEndReachedEvent !== `next-${pStatus.playlistTrackIndex}`) {
            sendPlayerCommand('next', {})
            broadcastTcpMessage(
              `next,${pStatus.playlist.playlistId},${pStatus.playlistTrackIndex}`
            )
            lastEndReachedEvent = `next-${pStatus.playlistTrackIndex}`
          }
        } else {
          sendPlayerCommand('stop_all', {})
          sendPlayerCommand('set_track_index', { index: 0 })
          broadcastTcpMessage('stop')
        }
      } else {
        logger.info('End of track reached, stopping playback.')
        sendPlayerCommand('stop', { idx: playerId })
      }
      break
    case 'all':
      if (pStatus.playlistMode) {
        logger.info('End of playlist reached, moving to next track.')
        if (lastEndReachedEvent !== `all-${pStatus.playlistTrackIndex}`) {
          sendPlayerCommand('next', {})
          broadcastTcpMessage(
            `next,${pStatus.playlist.playlistId},${pStatus.playlistTrackIndex}`
          )
          lastEndReachedEvent = `all-${pStatus.playlistTrackIndex}`
        }
      } else {
        sendPlayerCommand('stop', { idx: playerId })
        sendPlayerCommand('play', { idx: playerId })
        broadcastTcpMessage(`repeat`)
      }
      break
    case 'single':
      logger.info('End of single track reached, stopping playback.')
      sendPlayerCommand('stop', { idx: playerId })
      broadcastTcpMessage('stop')
      break
    case 'repeat_one':
      logger.info('Repeat one mode, restarting current track.')
      sendPlayerCommand('stop', { idx: playerId })
      sendPlayerCommand('play', { idx: playerId })
      broadcastTcpMessage(
        `next,${pStatus.playlist.playlistId},${pStatus.playlistTrackIndex}`
      )
      break
  }
}

async function handleMediaChanged(data) {
  logger.info(`Media changed event received: ${JSON.stringify(data)}`)

  let updated = false

  if (data.uuid) {
    const file = await dbFiles.findOne({ uuid: data.uuid })
    if (file) {
      pStatus.player[data.idx] = { ...pStatus.player[data.idx], file }
      logger.info(
        `Media changed for player ${data.idx}, file: ${file.filename}, uuid: ${file.uuid}`
      )
      updated = true
    }
  }

  if (typeof data.playlist_track_index === 'number') {
    if (pStatus.playlistTrackIndex !== data.playlist_track_index) {
      pStatus.playlistTrackIndex = data.playlist_track_index
      if (pStatus.tracks && pStatus.tracks[pStatus.playlistTrackIndex]) {
        pStatus.player[data.idx] = {
          ...pStatus.player[data.idx],
          file: pStatus.tracks[pStatus.playlistTrackIndex]
        }
        logger.info(
          `Media changed, current track set to index ${pStatus.playlistTrackIndex}, file: ${pStatus.player[data.idx].file.filename}`
        )
        updated = true
      }
    } else {
      logger.warn('Duplicate media_changed event detected, ignoring.')
      return
    }
  }

  if (updated) {
    sendMessageToClient('pStatus', {
      player: pStatus.player,
      playlistTrackIndex: pStatus.playlistTrackIndex
    })
  }
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
        case 'warn':
          logger.warn('Received warning message from Python:' + data)
          break
        case 'debug':
          logger.debug('Received debug message from Python:' + data)
          break
        case 'error':
          logger.error('Received error from Python:' + data)
          break
        case 'active_player_id':
          pStatus.activePlayerId = data.value
          sendMessageToClient('pStatus', {
            activePlayerId: pStatus.activePlayerId
          })
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
          sendMessageToClient('pStatus', { device: pStatus.device })
          break
        case 'set_image_time':
          pStatus.image_time = data.value || 5
          sendMessageToClient('pStatus', { image_time: pStatus.image_time })
          await dbStatus.update(
            { type: 'image_time' },
            { image_time: pStatus.image_time }
          )
          logger.info(`Image time set to ${pStatus.image_time}`)
          break
        case 'set_background':
          pStatus.background = data.background
          sendMessageToClient('pStatus', { background: data.background })
          await dbStatus.update(
            { type: 'background' },
            { value: data.background }
          )
          logger.info(`Background color set to ${data.background}`)
          break
        case 'set_fullscreen':
          pStatus.player.fullscreen = data.value
          sendMessageToClient('pStatus', {
            fullscreen: data.value
          })
          await dbStatus.update(
            { type: 'fullscreen' },
            { fullscreen: data.value }
          )
          logger.info(`Fullscreen mode set to ${data.value}`)
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
              playlist: pStatus.playlist,
              playlistTrackIndex: pStatus.playlistTrackIndex
            }
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
            { playlistTrackIndex: pStatus.playlistTrackIndex }
          )
          logger.info(`Playlist index set to ${pStatus.playlistTrackIndex}`)
          break
        case 'playlist_mode':
          pStatus.playlistMode = data.mode || false
          sendMessageToClient('pStatus', { playlistMode: pStatus.playlistMode })
          await dbStatus.update(
            { type: 'playlistMode' },
            { value: pStatus.playlistMode }
          )
          logger.info(`Playlist mode set to ${pStatus.playlistMode}`)
          break
        case 'track_index':
          pStatus.playlistTrackIndex = data.value || 0
          sendMessageToClient('pStatus', {
            playlistTrackIndex: pStatus.playlistTrackIndex
          })
          logger.info(
            `Playlist track index set to ${pStatus.playlistTrackIndex}`
          )
          break

        default:
          logger.warn(
            'Received unknown message type from Python: ' +
              JSON.stringify({ type, data })
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
