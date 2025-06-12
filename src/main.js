/** @format */

const { app, BrowerWindow } = require('electron')
const userDataPath = app.getPath('userData') // 사용자 데이터 경로
const { initDb } = require('./db')
initDb(userDataPath) // 데이터베이스 초기화

const { startPlayerProcess, stopPlayerProcess } = require('./player')
const logger = require('./logger')
const { getSetupfromDB } = require('./api/status')
const { initWeb } = require('./web')
const {
  existsMediaPath,
  existsTmpPath,
  existsLogoPath,
  deleteTmpFiles
} = require('./api/files/folders')
const { fnGetPlaylists } = require('./api/playlists')

// Electron이 준비되면 윈도우 생성
app.whenReady().then(async function () {
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
  const io = await initWeb(3000)
  startPlayerProcess(io) // Python 프로세스 시작
})
