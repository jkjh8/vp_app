const { spawn } = require('child_process')
const path = require('path')
const logger = require('@logger')
const { app } = require('electron')

let playerData = {}
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
    shell: false,
    env: {
      ...process.env,
      PYTHONIOENCODING: 'utf-8', // 파이썬 표준출력 인코딩 강제
      LANG: 'ko_KR.UTF-8' // 로케일도 한글로 강제(윈도우/리눅스 호환)
    }
  })

  pythonProcess.stdout.on('data', function (data) {
    // Node.js에서 출력 버퍼를 utf-8로 변환
    const lines = data.toString('utf8').split('\n').filter(Boolean)
    for (const line of lines) {
      try {
        const message = JSON.parse(line)
        console.log('Received message from Python:', message)
        if (message.type === 'info') {
          playerData = { ...playerData, ...message.data }
          // event가 MediaPlyaerPlaing인 경우. 현재 재생중인 파일 정보 전송
          if (playerData.event === 'EventType.MediaPlayerPlaying') {
            require('@api/player').sendCurrentFile()
          }
          if (playerData.event === 'EventType.MediaPlayerEndReached') {
            sendMessageToPython({ command: 'stop' })
          }
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
    pythonProcess.stdin.write(JSON.stringify(message) + '\n')
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
