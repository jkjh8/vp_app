const { pStatus } = require('../../_status.js')
const logger = require('../../logger')
const { dbStatus } = require('../../db')

const getSetupfromDB = async () => {
  // db에서 setup 정보를 가져와서 pStatus에 업데이트하고 반환
  const setups = await dbStatus.find()

  setups.forEach((setup) => {
    switch (setup.type) {
      case 'background':
        pStatus.background = setup.value
        break
      case 'playlistMode':
        pStatus.playlistMode = setup.value
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
          y: setup.y || 0,
          size: setup.size || 0
        }
        break
      case 'audiodevice':
        pStatus.device.audiodevice = setup.audiodevice
        break
      case 'fullscreen':
        pStatus.fullscreen = setup.fullscreen || false
        break
      case 'playlist':
        pStatus.playlist = setup.playlist || {}
        pStatus.playlistTrackIndex = setup.playlistTrackIndex || 0
        pStatus.tracks = setup.playlist.tracks || []
        break
      case 'repeat':
        if (pStatus.playlistMode === false && setup.mode === 'repeat_one') {
          pStatus.repeat = 'all'
        } else {
          pStatus.repeat = setup.mode || 'none'
        }
        break
      case 'image_time':
        pStatus.imageTime = setup.time || 5
        break
      default:
        logger.warn(`from db Unknown setup type: ${JSON.stringify(setup)}`)
    }
  })
  return pStatus
}

module.exports = {
  getSetupfromDB
}
