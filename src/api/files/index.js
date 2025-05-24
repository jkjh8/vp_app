const ffmpeg = require('fluent-ffmpeg')
const ffmpegPath = require('ffmpeg-static')
const ffprobe = require('ffprobe-static')
const logger = require('@logger')
const { v4: uuidv4 } = require('uuid')
const path = require('path')
const fs = require('fs')
const { tmpPath, mediaPath } = require('@api/files/folders')
const { generateThumbnail, resizeImage } = require('@api/files/thumbnail')
const { dbFiles } = require('@db')

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

// update된 파일 후처리 하기
const postProcessFiles = async (files) => {
  for (const file of files) {
    try {
      let thumbnailPath = null
      const { path: filePath, mimetype } = file
      // Generate a unique UUID for the file
      const uuid = uuidv4()
      // metadata를 가져오기
      const metadata = await getMetadata(filePath)
      // mediaPath아래 uuid 폴더 만들기
      const uuidFolderPath = path.join(mediaPath, uuid)
      await fs.promises.mkdir(uuidFolderPath, { recursive: true })
      const newFilePath = path.join(uuidFolderPath, file.originalname)
      // Move the file to the new location
      await fs.promises.rename(filePath, newFilePath)

      if (mimetype.startsWith('video/')) {
        // generateThumbnail이 썸네일 파일 경로를 반환한다고 가정
        thumbnailPath = await generateThumbnail(newFilePath, uuidFolderPath)
      } else if (mimetype.startsWith('image/')) {
        // resizeImage가 썸네일(작은 이미지) 파일 경로를 반환한다고 가정
        thumbnailPath = await resizeImage(newFilePath, uuidFolderPath)
      }
      await dbFiles
        .insert({
          ...file,
          uuid,
          path: newFilePath,
          metadata,
          thumbnail: thumbnailPath,
          createdAt: new Date(),
          updatedAt: new Date()
        })
        .then(() => {
          logger.info(`File processed and saved: ${newFilePath}`)
        })
    } catch (error) {
      logger.error('Error processing file:', error)
      throw error
    }
  }
}

module.exports = {
  setupFFmpeg,
  getMetadata,
  postProcessFiles
}
