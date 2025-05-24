/** @format */

import { createRequire } from 'module'
const require = createRequire(import.meta.url)
require('module-alias/register')
import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

// ES6에서 __dirname 대체
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

require('electron-reload')(__dirname, {
  electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron')
})

// 애플리케이션 윈도우 객체를 전역으로 유지
let mainWindow

// 윈도우 생성 함수 (화살표 함수로 변경)
const createWindow = () => {
  // 브라우저 윈도우 생성
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
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
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

// Electron이 준비되면 윈도우 생성
app.whenReady().then(() => {
  createWindow()

  // macOS에서는 앱이 활성화될 때 창이 없으면 새로 생성
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

// 모든 창이 닫히면 앱 종료 (Windows & Linux)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// 여기에 추가적인 메인 프로세스 코드 작성 가능

// IPC 통신 예시 (화살표 함수 사용)
// ipcMain.on('example-message', (event, arg) => {
//   console.log(`받은 메시지: ${arg}`) // 템플릿 리터럴 사용
//   event.reply('example-reply', 'pong')
// })
