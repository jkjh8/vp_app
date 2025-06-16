const net = require('net')
const { pStatus } = require('@/_status')
const logger = require('@logger')
const { handleMessage } = require('@/api/terminal')

// 연결된 소켓 목록
const tcpClients = []

let server = null

const initTcp = (port) => {
  if (!port) {
    port = pStatus.tcpPort
  }

  return new Promise((resolve, reject) => {
    server = net.createServer((socket) => {
      tcpClients.push(socket)
      logger.info('TCP client connected:', socket.remoteAddress)
      socket.write('Welcome!\n')

      socket.on('data', async (data) => {
        try {
          const message = data.toString('utf-8')
          logger.info(`TCP message received: ${message}`)
          const r = await handleMessage(message)
          socket.write(r + '\n')
        } catch (error) {
          socket.write('ERROR\n')
          logger.error('Error parsing data:', error)
        }
      })

      socket.on('close', () => {
        // 소켓 연결 종료 시 목록에서 제거
        const idx = tcpClients.indexOf(socket)
        if (idx !== -1) tcpClients.splice(idx, 1)
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

// 연결된 모든 TCP 클라이언트에 메시지 전송
function broadcastTcpMessage(msg) {
  tcpClients.forEach((socket) => {
    if (!socket.destroyed) {
      socket.write(msg + '\n')
    }
  })
}

module.exports = {
  initTcp,
  broadcastTcpMessage
}
