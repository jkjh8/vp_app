function handleMessage(msg) {
  try {
    // 메시지를 문자열로 변환 후 ',' 기준으로 분리
    const str = msg.toString().trim()
    const [command, ...params] = str.split(',')
    switch (command) {
      // player 관련 명령 처리 api/player 함수참고해서 명령체계 정리
      case 'playid':
        require('@api/player').playid(Number(params[0]))
        break
      case 'play':
        require('@api/player').play(Number(params[0]))
        break
      case 'stop':
        require('@api/player').stop()
        break
      case 'pause':
        require('@api/player').pause(Number(params[0]))
        break
      case 'time':
        require('@api/player').updateTime(
          Number(params[0]) * 1000,
          Number(params[1])
        )
        break
      case 'fullscreen':
        require('@api/player').setFullscreen(params[0] === 'true')
        break
      case 'logo':
        require('@api/player').setLogo(params[0])
        break
      case 'show_logo':
        require('@api/player').showLogo(params[0] === 'true')
        break
      case 'logo_size':
        require('@api/player').setLogoSize(Number(params[0]))
        break
      case 'background':
        require('@api/player').setBackground(params[0])
        break
    }
  } catch (error) {
    throw error
  }
}

module.exports = { handleMessage }
