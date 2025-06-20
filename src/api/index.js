const logger = require('../logger')
const { updatePStatus } = require('../_status.js')

const sendPlayerCommand = (command, data) => {
  // logger.info(`Sending command to player: ${command} ${data}`)
  require('../player').send({ command, ...data })
}

const sendMessageToClient = (event, data) => {
  const io = require('../web').getIO()
  if (!io) {
    logger.error('Socket.IO server is not initialized.')
    return
  }
  io.emit(event, data)
}

const sendStatusAndUpdate = async (stats) => {
  try {
    const io = require('../web').getIO()
    if (!io) {
      logger.error('Socket.IO server is not initialized.')
      return
    }

    // Validate stats before updating
    if (!stats || typeof stats !== 'object') {
      logger.error('Invalid stats object provided to sendStatusAndUpdate.')
      return
    }

    updatePStatus(stats)
    io.emit('pStatus', { ...stats })
    // logger.info('Status updated and sent to client successfully.')
  } catch (error) {
    logger.error('Error sending status and update:', error)
    return
  }
}

const broadcastTcpMessage = (message) => {
  require('../tcp').broadcastTcpMessage(message)
}

module.exports = {
  sendPlayerCommand,
  sendMessageToClient,
  sendStatusAndUpdate,
  broadcastTcpMessage
}
