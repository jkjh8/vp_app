/** @format */
const { app, powerSaveBlocker } = require('electron')
const userDataPath = app.getPath('userData') // 사용자 데이터 경로
const { initDb } = require('./db')
initDb(userDataPath) // 데이터베이스 초기화
const { pStatus } = require('./_status.js') // 상태 관리 모듈
const { startPlayerProcess, stopPlayerProcess } = require('./player')
const logger = require('./logger')
const { getSetupfromDB } = require('./api/status')
const { initTcp } = require('./tcp') // TCP 서버 초기화
const { initUdp } = require('./udp') // UDP 서버 초기화
const { initWeb } = require('./web')
const { playlistPlay } = require('./api/playlists')

const {
  existsMediaPath,
  existsTmpPath,
  existsLogoPath,
  deleteTmpFiles
} = require('./api/files/folders')
const { fnGetPlaylists } = require('./api/playlists')

let powerSaveId = null

// Electron이 준비되면 윈도우 생성
app.whenReady().then(async function () {
  // 전원 절전 모드 방지
  powerSaveId = powerSaveBlocker.start('prevent-app-suspension')
  logger.info('Power save blocker started with ID:', powerSaveId)
  // 미디어 및 임시 디렉토리 생성
  existsTmpPath() // 임시 디렉토리 확인 및 생성
  deleteTmpFiles() // 임시 디렉토리 내 모든 파일 삭제
  existsMediaPath() // 미디어 디렉토리 확인 및 생성
  existsLogoPath() // 로고 디렉토리 확인 및 생성
  // 데이터베이스 초기화
  await getSetupfromDB()
  // 플레이리스트 초기화
  await fnGetPlaylists()
  // http 서버 시작
  await initTcp(pStatus.tcpPort) // TCP 서버 시작
  await initUdp(pStatus.udpPort) // UDP 서버 시작
  // 웹 서버 시작
  await initWeb(pStatus.webPort)
  // start on playlist play
  if (pStatus.startOnPlaylist && pStatus.startOnPlaylist) {
    logger.info('Starting player process due to startOnPlaylist setting')
    setTimeout(async () => {
      await playlistPlay(pStatus.startOnPlaylist, 0)
    }, 1000)
  }
  startPlayerProcess() // Python 프로세스 시작
})

app.on('before-quit', () => {
  if (powerSaveId) {
    powerSaveBlocker.stop(powerSaveId) // 전원 절전 모드 방지 해제
    logger.info('Power save blocker stopped')
  }
})
