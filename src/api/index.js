const logger = require('../logger')
const { updatePStatus } = require('../_status.js')
const { pStatus } = require('../_status.js')

const commands = []
let commandInterval = null

function startCommandInterval() {
  if (!commandInterval) {
    commandInterval = setInterval(() => {
      if (pStatus.windowOpen && commands.length > 0) {
        const cmd = commands.shift()
        require('../player').send(cmd)
      }
      // 명령이 없으면 인터벌 중단
      if (commands.length === 0) {
        clearInterval(commandInterval)
        commandInterval = null
      }
    }, 100)
  }
}

const sendPlayerCommand = (command, data) => {
  commands.push({ command, ...data })
  startCommandInterval()
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
