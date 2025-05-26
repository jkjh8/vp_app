const appServer = require('@web')
const http = require('http')
const logger = require('@logger')

const { Server } = require('socket.io')
const { getPlayerData } = require('@py/index.js')

const httpServer = http.createServer(appServer)
const io = new Server(httpServer, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
})

io.on('connection', (socket) => {
  logger.info(`New client connected: ${socket.id}`)
  const rData = getPlayerData()
  if (rData) {
    socket.emit('player', JSON.stringify(rData))
  } else {
    logger.warn('No player data available to send')
  }

  // Handle disconnection
  socket.on('disconnect', () => {
    logger.info(`Client disconnected: ${socket.id}`)
  })

  // You can add more event listeners here
  // Example: socket.on('message', (data) => { ... })
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

    // Start the Python process with the Socket.IO instance
    // startPythonProcess(io)
  } catch (error) {
    logger.error('Error initializing Socket.IO server:', error)
  }
  return io
}

module.exports = {
  initIOServer,
  io
}
