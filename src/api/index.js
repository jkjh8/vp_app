const logger = require('@logger')
const sendPlayerCommand = (command, data) => {
  logger.info(`Sending command to player: ${command}`, data)
  require('@py').send({ command, ...data })
}

const sendMessageToClient = (event, data) => {
  const io = require('@web/io').getIO()
  if (!io) {
    logger.error('Socket.IO server is not initialized.')
    return
  }
  io.emit(event, data)
}

module.exports = {
  sendPlayerCommand,
  sendMessageToClient
}
