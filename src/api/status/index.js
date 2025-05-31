const db = require('@db')
const { pStatus } = require('@src/_status.js')
const logger = require('@logger')

const getSetupfromDB = async () => {
  // db에서 setup 정보를 가져와서 pStatus에 업데이트하고 반환
  const setups = await db.status.find()
  setups.forEach((setup) => {
    switch (setup.type) {
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
          show: setup.value.show || false,
          file: setup.value.file || '',
          width: setup.value.width || 0,
          height: setup.value.height || 0,
          x: setup.value.x || 0,
          y: setup.value.y || 0
        }
        break

      default:
        logger.warn(`Unknown setup type: ${setup.type}`)
    }
  })
  return pStatus
}

module.exports = {
  getSetupfromDB
}
