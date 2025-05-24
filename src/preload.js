/** @format */

// preload.js
const { contextBridge, ipcRenderer } = require('electron')

// 렌더러 프로세스에서 사용할 API를 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // 메인 프로세스에 메시지 보내기
  sendMessage: (channel, data) => {
    ipcRenderer.send(channel, data)
  },

  // 메인 프로세스로부터 응답 받기
  on: (channel, callback) => {
    ipcRenderer.on(channel, (event, ...args) => callback(...args))
  }
})

// 페이지가 로드되었을 때 실행되는 코드
window.addEventListener('DOMContentLoaded', () => {
  console.log('DOM 로드 완료!')

  // 페이지에 있는 요소를 수정할 수 있습니다
  const replaceText = (selector, text) => {
    const element = document.getElementById(selector)
    if (element) element.innerText = text
  }

  // 버전 정보 표시 예시 (필요시 활성화)
  // for (const dependency of ['chrome', 'node', 'electron']) {
  //   replaceText(`${dependency}-version`, process.versions[dependency])
  // }
})
