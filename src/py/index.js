const { spawn } = require('child_process')
const path = require('path')
const logger = require('../logger/index.js')
const { app } = require('electron')

let playerData = null
let pythonProcess = null
const pythonPath = path.join(__dirname, '.venv', 'Scripts', 'python.exe')
const pythonScriptPath = path.join(__dirname, 'player.py')

function startPythonProcess(io) {
  if (pythonProcess) {
    logger.warn('Python process is already running.')
    return
  }

  pythonProcess = spawn(pythonPath, [pythonScriptPath], {
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: false
  })

  pythonProcess.stdout.on('data', function (data) {
    const lines = data.toString().split('\n').filter(Boolean)
    for (const line of lines) {
      try {
        const message = JSON.parse(line)
        if (message.type === 'info') {
          playerData = message.data
          if (io && io.emit) {
            io.emit('player', playerData)
          }
        } else if (message.type === 'error') {
          logger.error('Python error:', message.data)
        } else {
          logger.warn('Unknown message type from Python:', message.type)
        }
      } catch (error) {
        logger.error('Error parsing JSON from Python:', error, '원본:', line)
      }
    }
  })

  pythonProcess.stderr.on('data', function (data) {
    logger.error('Python stderr: ' + data)
  })

  pythonProcess.on('close', function (code) {
    logger.info('Python process exited with code ' + code)
    pythonProcess = null
    if (!app.isQuiting) {
      app.quit()
    }
  })

  logger.info('Python process has been start.')
}

function stopPythonProcess() {
  if (!pythonProcess) {
    logger.warn('Python process is not running.')
    return
  }
  pythonProcess.kill()
  pythonProcess = null
  logger.info('Python process has been terminated.')
}

function sendMessageToPython(message) {
  if (!pythonProcess) {
    logger.warn('Python process is not running.')
    return
  }
  if (pythonProcess.stdin.writable) {
    pythonProcess.stdin.write(message + '\n')
    logger.info('Sent message to Python: ' + message)
  } else {
    logger.error('Python process stdin is not writable.')
  }
}

function getPlayerData() {
  return playerData
}

module.exports = {
  startPythonProcess,
  stopPythonProcess,
  sendMessageToPython,
  getPlayerData
}
