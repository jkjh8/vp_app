const ffmpeg = require('fluent-ffmpeg')
const ffmpegPath = require('ffmpeg-static')
const ffprobe = require('ffprobe-static')
const logger = require('@logger')

const setupFFmpeg = () => {
  let ffmpegExecutablePath = ffmpegPath.replace('app.asar', 'app.asar.unpacked')
  let ffprobeExecutablePath = ffprobe.path.replace(
    'app.asar',
    'app.asar.unpacked'
  )
  logger.info('ffmpeg path:', ffmpegExecutablePath)
  logger.info('ffprobe path:', ffprobeExecutablePath)
  ffmpeg.setFfmpegPath(ffmpegExecutablePath)
  ffmpeg.setFfprobePath(ffprobeExecutablePath)
}

// getVideoMetadata 함수는 비디오 파일의 메타데이터를 가져오는 Promise를 반환합니다.
const getMetadata = (filePath) => {
  return new Promise((resolve, reject) => {
    ffmpeg.ffprobe(filePath, (err, metadata) => {
      if (err) {
        logger.error('Error getting video metadata:', err)
        reject(err)
      } else {
        resolve(metadata)
      }
    })
  })
}

module.exports = {
  setupFFmpeg,
  getMetadata
}
