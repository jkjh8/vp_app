const { app } = require('electron')
const path = require('path')
const fs = require('fs')
const logger = require('@logger')

function getMediaPath() {
  return path.join(app.getPath('home'), 'media')
}
function getTmpPath() {
  return path.join(app.getPath('userData'), 'tmp')
}

function existsMediaPath() {
  const mediaPath = getMediaPath()
  if (!fs.existsSync(mediaPath)) {
    fs.mkdirSync(mediaPath, { recursive: true })
    logger.info(`Media path created: ${mediaPath}`)
  } else {
    logger.info(`Media path exists: ${mediaPath}`)
  }
}

function existsTmpPath() {
  const tmpPath = getTmpPath()
  if (!fs.existsSync(tmpPath)) {
    fs.mkdirSync(tmpPath, { recursive: true })
    logger.info(`Tmp path created: ${tmpPath}`)
  } else {
    logger.info(`Tmp path exists: ${tmpPath}`)
  }
}

function deleteTmpFiles() {
  const tmpPath = getTmpPath()
  fs.readdir(tmpPath, (err, files) => {
    if (err) {
      logger.error(`Error reading tmp directory: ${err}`)
      return
    }
    files.forEach((file) => {
      const filePath = path.join(tmpPath, file)
      fs.unlink(filePath, (err) => {
        if (err) {
          logger.error(`Error deleting tmp file: ${err}`)
        } else {
          logger.info(`Tmp file deleted: ${filePath}`)
        }
      })
    })
  })
}

module.exports = {
  getMediaPath,
  getTmpPath,
  existsMediaPath,
  existsTmpPath,
  deleteTmpFiles
}
