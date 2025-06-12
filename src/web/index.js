const path = require('path')
const { app } = require('electron')
const express = require('express')
const cookieParser = require('cookie-parser')
const cors = require('cors')
const httpLogger = require('morgan')
const http = require('http')
const logger = require('../logger')
const { Server } = require('socket.io')
const { pStatus } = require('../_status')
const { parsing } = require('./io')

let io = null

const initWeb = (httpPort) => {
  return new Promise((resolve, reject) => {
    try {
      const port = httpPort || process.env.PORT || 3000
      logger.info(`Web server port: ${port}`)

      const appServer = express()
      const publicFolder = path.join(app.getAppPath(), 'public')

      appServer.use(express.json())
      appServer.use(express.urlencoded({ extended: true }))
      appServer.use(cookieParser())
      appServer.use(cors())

      // 개발 환경에서만 morgan 사용
      if (process.env.NODE_ENV === 'development') {
        appServer.use(httpLogger('dev'))
      }

      appServer.use(express.static(path.join(publicFolder, 'spa')))
      appServer.use('/', require('./routes'))

      const httpServer = http.createServer(appServer)

      io = new Server(httpServer, {
        cors: {
          origin: '*',
          methods: ['GET', 'POST']
        }
      })

      io.on('connection', (socket) => {
        logger.info(`New client connected: ${socket.id}`)
        socket.emit('pStatus', pStatus)
        socket.on('event', parsing)
        socket.on('disconnect', () =>
          logger.info(`Client disconnected: ${socket.id}`)
        )
      })

      httpServer.listen(port, () => {
        logger.info(`Socket.IO server running on port ${port}`)
        resolve(io)
      })
    } catch (error) {
      logger.error('Error initializing Socket.IO server:', error)
      reject(error)
    }
  })
}

const getIO = () => io

module.exports = { initWeb, getIO }
