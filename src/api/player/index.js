const socket = require('@web/io')
const { sendMessageToPython } = require('@py/index.js')
const db = require('@db')
const logger = require('@logger')

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)

  if (!id) {
    sendMessageToPython('play')
    return 'Playing without ID'
  }

  const file = await db.files.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }

  sendMessageToPython(`play:${file.path}`)

  return `Playing file: ${file.path}`
}

const play = () => {
  logger.info('Received play request without ID')
  sendMessageToPython('play')
  return 'Playing without ID'
}

const pause = () => {
  logger.info('Received pause request')
  sendMessageToPython('pause')
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  sendMessageToPython('stop')
  return 'Player stopped'
}

const sendPlayerData = (data) => {
  socket.io.emit('player', data)
}

module.exports = {
  playid,
  play,
  stop,
  pause,
  sendPlayerData
}
