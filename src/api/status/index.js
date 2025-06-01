const db = require('@db')
const { pStatus } = require('@src/_status.js')
const logger = require('@logger')

const getSetupfromDB = async () => {
  // db에서 setup 정보를 가져와서 pStatus에 업데이트하고 반환
  const setups = await db.status.find()

  setups.forEach((setup) => {
    switch (setup.type) {
      case 'image_time':
        pStatus.image_time = setup.time
        break
      case 'background':
        pStatus.background = setup.value
        break
      case 'playlistmode':
        pStatus.playlistmode = setup.value
        break
      case 'repeat':
        pStatus.repeat = setup.value
        break
      case 'darkmode':
        pStatus.darkmode = setup.value
        break
      case 'playlistfile':
        pStatus.playlistfile = setup.value
        break
      case 'playlist':
        pStatus.playlist = setup.value
        break
      case 'device':
        pStatus.device.audiocurrentdevice = setup.value
        break
      case 'logo':
        pStatus.logo = {
          show: setup.show || false,
          name: setup.name || '',
          file: setup.file || '',
          width: setup.width || 0,
          height: setup.height || 0,
          x: setup.x || 0,
          y: setup.y || 0
        }
        break
      case 'audiodevice':
        console.log('Setting audio device from DB:', setup.audiodevice)
        pStatus.device.audiodevice = setup.audiodevice
        break
      case 'fullscreen':
        pStatus.player.fullscreen = setup.fullscreen || false
        break
      default:
        logger.warn(`Unknown setup type: ${JSON.stringify(setup)}`)
    }
  })
  return pStatus
}

module.exports = {
  getSetupfromDB
}
