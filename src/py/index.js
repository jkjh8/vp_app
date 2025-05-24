const { spawn } = require('child_process')
const path = require('path')
const logger = require('../logger/index.js')
const { app } = require('electron')

let pythonProcess = null
const pythonPath = path.join(__dirname, '.venv', 'Scripts', 'python.exe')
const pythonScriptPath = path.join(__dirname, 'player.py')

function startPythonProcess() {
  if (pythonProcess) {
    logger.warn('Python process is already running.')
    return
  }

  pythonProcess = spawn(pythonPath, [pythonScriptPath], {
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false
  })

  pythonProcess.stdout.on('data', function (data) {
    console.log('Python stdout: ' + data)
  })

  pythonProcess.stderr.on('data', function (data) {
    logger.error('Python stderr: ' + data)
  })

  pythonProcess.on('close', function (code) {
    logger.info('Python process exited with code ' + code)
    pythonProcess = null
    // 파이썬 프로세스가 종료되면 앱도 종료
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

  pythonProcess.stdin.write(JSON.stringify(message) + '\n')
}

module.exports = {
  startPythonProcess,
  stopPythonProcess,
  sendMessageToPython
}
