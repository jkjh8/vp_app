const dgram = require('dgram')
const { pStatus } = require('../_status')
const logger = require('../logger')
const { handleMessage } = require('../api/terminal')
const initUdp = (port) => {
  if (!port) {
    port = pStatus.udpPort
  }
  return new Promise((resolve, reject) => {
    dgram
      .createSocket('udp4', (msg, rinfo) => {
        try {
          const message = msg.toString('utf-8')
          handleMessage(message)
        } catch (error) {
          logger.error('Error parsing UDP message:', error)
        }
      })
      .bind(port, () => {
        logger.info(`UDP server listening on port ${port}`)
        resolve()
      })
      .on('error', (err) => {
        logger.error('UDP server error:', err)
        reject(err)
      })
  })
}

module.exports = {
  initUdp
}
