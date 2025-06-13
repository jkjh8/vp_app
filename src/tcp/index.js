const net = require('net')
const { pStatus } = require('@/_status')
const logger = require('@logger')

const initTcp = (port) => {
  if (!port) {
    port = pStatus.tcpPort
  }
  return new Promise((resolve, reject) => {
    const server = net.createServer((socket) => {
      socket.on('data', (data) => {
        try {
          const message = data.toString('utf-8')
          logger.info(`TCP message received: ${message}`)
        } catch (error) {
          logger.error('Error parsing data:', error)
        }
      })

      socket.on('error', (err) => {
        logger.error('Socket error:', err)
      })
    })

    server.listen(port, () => {
      logger.info(`TCP server listening on port ${port}`)
      resolve(server)
    })

    server.on('error', (err) => {
      logger.error('Server error:', err)
      reject(err)
    })
  })
}

module.exports = {
  initTcp
}
