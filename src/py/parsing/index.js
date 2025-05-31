let { pStatus } = require('@src/_status.js')
const logger = require('@logger')

function handleInfoMessage(message) {
  pStatus = { ...pStatus, ...message.data }
  const { io } = require('@web/io')
  if (io && io.emit) {
    io.emit('pStatus', pStatus)
  }
}

function handleErrorMessage(message) {
  logger.error('Python error:', message.data)
}

function handleUnknownMessage(message) {
  logger.warn(`Unknown message type from Python:${message.data}`)
}

const parsing = (data) => {
  const lines = data.toString('utf8').split('\n').filter(Boolean)
  for (const line of lines) {
    try {
      const message = JSON.parse(line)
      switch (message.type) {
        case 'info':
          handleInfoMessage(message)
          break
        case 'stop':
          logger.info(`Received stop command from Python:${message.data}`)
          require('@py').sendMessageToPython({ command: 'stop' })
          break
        case 'event':
          switch (message.data.event) {
            case 'end_reached':
              switch (pStatus.repeat) {
                case 'none':
                  if (pStatus.playlistmode) {
                    if (
                      pStatus.playlist.length > 0 &&
                      message.data.playlist_index < pStatus.playlist.length - 1
                    ) {
                      logger.info(
                        `End of track reached(none), moving to next track in playlist. Current index: ${message.data.playlist_index}`
                      )
                      require('@py').sendMessageToPython({ command: 'next' })
                    } else {
                      require('@py').sendMessageToPython({ command: 'stop' })
                    }
                  } else {
                    logger.info('End of track reached, stopping playback.')
                    require('@py').sendMessageToPython({ command: 'stop' })
                  }
                  break
                case 'all':
                  if (pStatus.playlistmode) {
                    logger.info('End of playlist reached, stopping playback.')
                    require('@py').sendMessageToPython({ command: 'next' })
                  } else {
                    logger.info('End of track reached, stopping playback.')
                    require('@py').sendMessageToPython({ command: 'stop' })
                    require('@py').sendMessageToPython({ command: 'play' })
                  }
                  break
                case 'single':
                  logger.info('End of single track reached, stopping playback.')
                  require('@py').sendMessageToPython({ command: 'stop' })
                  break
                case 'repeat_one':
                  logger.info('Repeat one mode, restarting current track.')
                  require('@py').sendMessageToPython({ command: 'stop' })
                  require('@py').sendMessageToPython({ command: 'play' })
                  break
              }
              break
            case 'media_changed':
              pStatus.playlistindex = message.data.playlist_index
              if (pStatus.playlistmode && pStatus.playlistindex >= 0) {
                logger.info(
                  `Media changed, updating current track index to ${pStatus.playlistindex}`
                )
                pStatus.current = pStatus.playlist[pStatus.playlistindex]
              } else {
                logger.info('Media changed, resetting current track index.')
                pStatus.current = null
              }
              break
            default:
              logger.warn(
                `Unknown player event from Python:${message.data.event}`
              )
              break
          }
        case 'message':
          if (typeof message.data !== 'string') {
            logger.warn(
              `Received non-string message from Python:${JSON.stringify(message.data)}`
            )
            return
          }
          console.log(`Received message from Python:${message.data}`)
          break
        case 'error':
          handleErrorMessage(message)
          break
        default:
          handleUnknownMessage(message)
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
