const { app } = require('electron')
const path = require('path')
const fs = require('fs')
const logger = require('@logger')

const mediaPath = path.join(app.getPath('home'), 'media')
const tmpPath = path.join(app.getPath('userData'), 'tmp')

// mediaPath를 확인하고 없으면 만들기
const existsMediaPath = () => {
  if (!fs.existsSync(mediaPath)) {
    fs.mkdirSync(mediaPath, { recursive: true })
    logger.info('Media path created:', mediaPath)
  }
}

// tmpPath를 확인하고 없으면 만들기
const existsTmpPath = () => {
  if (!fs.existsSync(tmpPath)) {
    fs.mkdirSync(tmpPath, { recursive: true })
    logger.info('Tmp path created:', tmpPath)
  }
}

// tmpPath 내 모든 파일 삭제
const deleteTmpFiles = () => {
  fs.readdir(tmpPath, (err, files) => {
    if (err) {
      logger.error('Error reading tmp directory:', err)
      return
    }
    files.forEach((file) => {
      const filePath = path.join(tmpPath, file)
      fs.unlink(filePath, (err) => {
        if (err) {
          logger.error('Error deleting tmp file:', err)
        } else {
          logger.info('Tmp file deleted:', filePath)
        }
      })
    })
  })
}

module.exports = {
  mediaPath,
  tmpPath,
  existsMediaPath,
  existsTmpPath,
  deleteTmpFiles
}
