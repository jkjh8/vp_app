let { pStatus } = require('@src/_status.js')
const { getIO } = require('@web/io')
const logger = require('@logger')

function handleInfoMessage(message) {
  pStatus = { ...pStatus, ...message.data }
  if (getIO() && getIO().emit) {
    getIO().emit('pStatus', pStatus)
  }
}

function handleErrorMessage(message) {
  logger.error('Python error:', message.data)
}

function handleUnknownMessage(message) {
  logger.warn('Unknown message type from Python:', message.data)
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
          logger.info('Received stop command from Python:', message.data)
          require('@py').sendMessageToPython({ command: 'stop' })
          break
        case 'message':
          logger.info('Received message from Python:', message.message)

          break
        case 'error':
          handleErrorMessage(message)
          break
        default:
          handleUnknownMessage(message)
          break
      }
    } catch (error) {
      logger.error('Error parsing JSON from Python:', error, 'Original:', line)
    }
  }
}

module.exports = {
  parsing
}
