const { spawn } = require('child_process')
const { app } = require('electron')
const path = require('path')
const logger = require('@logger')
const {
  pStatus,
  getPythonProcess,
  setPythonProcess
} = require('@src/_status.js')
const { parsing } = require('./parsing')
const {} = require('@src/_status.js')

const pythonPath = path.join(__dirname, '.venv', 'Scripts', 'python.exe')
const pythonScriptPath = path.join(__dirname, 'player.py')

function startPythonProcess() {
  if (getPythonProcess()) {
    logger.warn('Python process is already running.')
    return
  }
  // pStatus를 환경변수로 전달
  const proc = spawn(pythonPath, [pythonScriptPath], {
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: false,
    env: {
      ...process.env,
      PYTHONIOENCODING: 'utf-8',
      LANG: 'ko_KR.UTF-8',
      VP_PSTATUS: JSON.stringify(pStatus) // pStatus를 JSON 문자열로 전달
    }
  })

  proc.stdout.on('data', parsing)
  proc.stderr.on('data', (data) => logger.error('Python stderr: ' + data))
  proc.on('close', (code) => {
    logger.info('Python process exited with code ' + code)
    setPythonProcess(null)
    if (!app.isQuiting) app.quit()
  })
  setPythonProcess(proc)
  logger.info('Python process started with PID: ' + proc.pid)
}

function stopPythonProcess() {
  const proc = getPythonProcess()
  if (!proc) {
    logger.warn('Python process is not running.')
    return
  }
  proc.kill()
  setPythonProcess(null)
  logger.info('Python process has been terminated.')
}

function sendMessageToPython(message) {
  const proc = getPythonProcess()
  if (!proc) {
    logger.warn('Python process is not running.')
    return
  }
  if (proc.stdin.writable) {
    proc.stdin.write(JSON.stringify(message) + '\n')
    logger.info('Sent message to Python: ' + message)
  } else {
    logger.error('Python process stdin is not writable.')
  }
}

function getAudioDevices() {
  const proc = getPythonProcess()
  if (!proc) {
    logger.warn('Python process is not running.')
    return []
  }
  sendMessageToPython({ command: 'get_audio_devices' })
}

module.exports = {
  startPythonProcess,
  stopPythonProcess,
  sendMessageToPython,
  getAudioDevices
}
