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
const pythonScriptPath = path.join(__dirname, 'player', 'player.py')

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
      ...process.env, // 기존 환경변수 유지
      encoding: 'utf-8',
      VP_PSTATUS: JSON.stringify(pStatus), // pStatus를 JSON 문자열로 전달
      PYTHONIOENCODING: 'utf-8' // Python 출력 인코딩 설정
    }
  })

  proc.stdout.on('data', parsing)
  proc.stderr.on('data', (data) => logger.error('Python stderr: ' + data))
  proc.on('close', (code) => {
    logger.warn('Python process exited with code ' + code)
    app.quit() // Python 프로세스가 종료되면 앱도 종료
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
  logger.info('Python process has been terminated.')
}

function send(message) {
  const proc = getPythonProcess()
  if (!proc) {
    logger.warn('Python process is not running.')
    return
  }
  if (proc.stdin.writable) {
    const jsonMsg = JSON.stringify(message)
    proc.stdin.write(jsonMsg + '\n')
    logger.info('Sent message to Python: ' + jsonMsg)
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
  send({ command: 'get_audio_devices' })
}

module.exports = {
  startPythonProcess,
  stopPythonProcess,
  send,
  getAudioDevices
}
