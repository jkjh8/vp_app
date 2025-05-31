/** @format */

// import { createRequire } from 'module'
// const require = createRequire(import.meta.url)
require('module-alias/register')
const electron = require('electron')
const app = electron.app
const BrowserWindow = electron.BrowserWindow
const path = require('path')

const { startPythonProcess } = require('@py')
const { stopPythonProcess } = require('@py')
const logger = require('@logger')
require('@db')
const { getSetupfromDB } = require('@api/status')
const { initIOServer } = require('@web/io')
const {
  existsMediaPath,
  existsTmpPath,
  existsLogoPath,
  deleteTmpFiles
} = require('@api/files/folders')
const { start } = require('repl')

// ES5에서는 __dirname, __filename 바로 사용 가능

// 애플리케이션 윈도우 객체를 전역으로 유지
let mainWindow

// 윈도우 생성 함수
function createWindow() {
  // 브라우저 윈도우 생성
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    x: 100, // 창의 x 좌표
    y: 100, // 창의 y 좌표
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  })

  // index.html 로드
  mainWindow.loadFile(path.join(__dirname, 'index.html'))
  mainWindow.webContents.openDevTools() // 조건 없이 항상 실행

  // 윈도우가 닫힐 때 발생하는 이벤트
  mainWindow.on('closed', function () {
    mainWindow = null
    logger.info('Main window has been closed.')
  })
}

// Electron이 준비되면 윈도우 생성
app.whenReady().then(async function () {
  // 미디어 및 임시 디렉토리 생성
  existsTmpPath() // 임시 디렉토리 확인 및 생성
  deleteTmpFiles() // 임시 디렉토리 내 모든 파일 삭제
  existsMediaPath() // 미디어 디렉토리 확인 및 생성
  existsLogoPath() // 로고 디렉토리 확인 및 생성
  //데이터 베이스 초기화
  await getSetupfromDB()
  // http 서버 시작
  const io = initIOServer(3000)
  // startPythonProcess()
  startPythonProcess(io) // Python 프로세스 시작
  // createWindow()

  // macOS에서는 앱이 활성화될 때 창이 없으면 새로 생성
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) {
      // createWindow()
    }
  })
})

// 모든 창이 닫히면 앱 종료 (Windows & Linux)
app.on('window-all-closed', function () {
  // python 프로세스 종료
  stopPythonProcess()
  if (process.platform !== 'darwin') {
    app.quit()
  }
  logger.info('All windows have been closed and the app is quitting.')
})

// 여기에 추가적인 메인 프로세스 코드 작성 가능

// IPC 통신 예시 (화살표 함수 사용)
// ipcMain.on('example-message', (event, arg) => {
//   console.log(`받은 메시지: ${arg}`) // 템플릿 리터럴 사용
//   event.reply('example-reply', 'pong')
// })
