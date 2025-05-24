const appServer = require('@web')
const http = require('http')
const logger = require('@logger')

const { Server } = require('socket.io')

const httpServer = http.createServer(appServer)
const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
})

const initIOServer = (httpPort) => {
  try {
    let port = null
    if (httpPort) {
      port = httpPort
    } else {
      port = process.env.PORT || 3000
    }
    httpServer.listen(port, () => {
      logger.info(`Socket.IO server running on port ${port}`)
    })
  } catch (error) {
    logger.error('Error initializing Socket.IO server:', error)
  }
}

module.exports = {
  initIOServer,
  io
}
