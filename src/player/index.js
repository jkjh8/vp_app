const { spawn } = require('child_process')
const { app } = require('electron')
const path = require('path')
const logger = require('../logger')
const { pStatus, getPythonProcess, setPlayerProcess } = require('../_status.js')
const { parsing } = require('./parsing')

function startPlayerProcess() {
  try {
    if (getPythonProcess()) {
      logger.warn('Python process is already running.')
      return
    }
    const pythonPath = path.join(
      app.getAppPath(),
      'src',
      'player',
      'player',
      '.venv',
      'Scripts',
      'python.exe'
    )
    const scriptPath = path.join(
      app.getAppPath(),
      'src',
      'player',
      'player',
      'player.py'
    )
    // 개발 환경에서는 src/player/player.exe, 빌드(패키징) 환경에서는 루트 위치의 player.exe 사용
    // let scriptPath
    // if (app.isPackaged) {
    //   // 패키징된 환경: player.exe는 resources 폴더에 위치
    //   scriptPath = path.join('player.exe')
    // } else {
    //   // 개발 환경: package.json 기준 상대경로로 player.exe 위치 지정
    //   scriptPath = path.join(app.getAppPath(), 'src', 'player', 'player.exe')
    // }
    // asar 패키징된 환경에서는 app.asar.unpacked 경로로 변경
    // scriptPath.replace('app.asar', 'app.asar.unpacked')

    const proc = spawn(pythonPath, [scriptPath], {
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: false,
      env: {
        ...process.env, // 기존 환경변수 유지
        encoding: 'utf-8',
        VP_PSTATUS: JSON.stringify(pStatus), // pStatus를 JSON 문자열로 전달
        APP_PATH: app.getAppPath(), // 앱 경로 전달
        PYTHONIOENCODING: 'utf-8' // Python 출력 인코딩 설정
      }
    })

    proc.stdout.on('data', parsing)
    proc.stderr.on('data', (data) => logger.error('Python stderr: ' + data))
    proc.on('close', (code) => {
      logger.warn('Python process exited with code ' + code)
      app.quit() // Python 프로세스가 종료되면 앱도 종료
    })
    setPlayerProcess(proc)
    logger.info('Python process started with PID: ' + proc.pid)
  } catch (error) {
    logger.error('Error starting Python process:', error)
    app.quit() // 에러 발생 시 앱 종료
  }
}

function stopPlayerProcess() {
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
    // logger.info('Sent message to Python: ' + jsonMsg)
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
  startPlayerProcess,
  stopPlayerProcess,
  send,
  getAudioDevices
}
