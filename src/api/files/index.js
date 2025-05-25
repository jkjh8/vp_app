const ffmpeg = require('fluent-ffmpeg')
const ffmpegPath = require('ffmpeg-static')
const ffprobe = require('ffprobe-static')
const logger = require('@logger')
const { v4: uuidv4 } = require('uuid')
const path = require('path')
const fs = require('fs')
const { getTmpPath, getMediaPath } = require('@api/files/folders')
const { generateThumbnail, resizeImage } = require('@api/files/thumbnail')
const db = require('@db')

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

// 파일 등록 시 중복되지 않는 숫자(순번) 생성 함수
const getNextFileNumber = async () => {
  const lastFiles = await db.files.find({}).sort({ number: -1 }).limit(1)
  return lastFiles.length > 0 ? lastFiles[0].number + 1 : 1
}

// number만 미리 등록(예약)
const reserveFileNumber = async () => {
  const number = await getNextFileNumber()
  // 임시로 uuid만 넣고 number만 등록
  const uuid = uuidv4()
  await db.files.insert({
    uuid,
    number,
    reserved: true,
    createdAt: new Date(),
    updatedAt: new Date()
  })
  return { uuid, number }
}

// update된 파일 후처리 하기
const postProcessFiles = async (files) => {
  const mediaPath = getMediaPath()
  const tmpPath = getTmpPath()

  for (const file of files) {
    try {
      let thumbnailPath = null
      const {
        path: filePath,
        mimetype,
        fieldname,
        filename,
        size,
        originalname
      } = file

      // number와 uuid 미리 예약
      const { uuid, number } = await reserveFileNumber()

      // metadata를 가져오기
      const metadata = await getMetadata(filePath)
      // mediaPath아래 uuid 폴더 만들기
      const uuidFolderPath = path.join(mediaPath, uuid)
      await fs.promises.mkdir(uuidFolderPath, { recursive: true })
      const newFilePath = path.join(uuidFolderPath, file.originalname)
      // Move the file to the new location
      await fs.promises.rename(filePath, newFilePath)

      if (mimetype.startsWith('video/')) {
        thumbnailPath = await generateThumbnail(newFilePath, uuidFolderPath)
      } else if (mimetype.startsWith('image/')) {
        thumbnailPath = await resizeImage(newFilePath, uuidFolderPath)
      }

      // 예약된 number와 uuid로 파일 정보 업데이트
      await db.files.update(
        { uuid, number },
        {
          $set: {
            reserved: false,
            fieldname,
            filename,
            originalname,
            amx: convertforAMX(originalname),
            mimetype,
            size,
            path: newFilePath,
            metadata,
            thumbnail: thumbnailPath,
            updatedAt: new Date()
          }
        }
      )
      logger.info(`File processed and saved: ${newFilePath}`)
    } catch (error) {
      logger.error('Error processing file:', error)
      throw error
    }
  }
}

const insertFileWithUniqueNumber = async (fileData) => {
  let retry = 0
  while (retry < 5) {
    const number = await getNextFileNumber()
    try {
      await db.files.insert({ ...fileData, number })
      return
    } catch (err) {
      if (err.errorType === 'uniqueViolated') {
        retry++
        continue
      }
      throw err
    }
  }
  throw new Error('Failed to insert file with unique number after retries')
}

// utf-8을 amx tp에서 사용하는 스트링으로 변환하는 함수
const convertforAMX = (str) => {
  const encoder = new TextEncoder('utf-16le')
  const encoded = encoder.encode(str)
  const hexArray = Array.from(encoded)
    .map((byte) => byte.toString(16).padStart(4, '0'))
    .join(',')

  return hexArray
}

module.exports = {
  setupFFmpeg,
  getMetadata,
  postProcessFiles,
  insertFileWithUniqueNumber,
  convertforAMX
}
