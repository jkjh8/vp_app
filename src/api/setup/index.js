const db = require('@db')
const { pStatus } = require('@src/_status.js')
const logger = require('@logger')

const initSetup = async () => {
  try {
    const setups = await db.setup.find()
    if (setups.length === 0) {
      return logger.warn('No setup found, initializing default setup...')
    }
    for (const setup of setups) {
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
    }
  } catch (error) {
    logger.error('Error during setup initialization:', error)
  }
}
