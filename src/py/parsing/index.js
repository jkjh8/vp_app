let { pStatus } = require('@src/_status.js')
const { getIO } = require('@web/io')

const parsing = (data) => {
  const lines = data.toString('utf8').split('\n').filter(Boolean)
  for (const line of lines) {
    try {
      const message = JSON.parse(line)
      console.log('Received message from Python:', message)

      if (message.type === 'info') {
        pStatus = { ...pStatus, ...message.data }
        if (pStatus.player.event === 'EventType.MediaPlayerEndReached') {
          getIO().emit('command', { command: 'stop' })
        }
        if (getIO() && getIO().emit) {
          getIO().emit('pStatus', pStatus)
        }
      } else if (message.type === 'error') {
        console.error('Python error:', message.data)
      } else {
        console.warn('Unknown message type from Python:', message.type)
      }
    } catch (error) {
      console.error('Error parsing JSON from Python:', error, 'Original:', line)
    }
  }
}

module.exports = {
  parsing
}
