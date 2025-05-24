const ffmpeg = require('fluent-ffmpeg')
const path = require('path')

const generateThumbnail = (filePath, outputPath, time = 5) => {
  return new Promise((resolve, reject) => {
    const baseName = path.parse(filePath).name
    const thumbnailName = `thumbnail-${baseName}.png`
    ffmpeg(filePath)
      .on('end', () => {
        resolve(path.join(outputPath, thumbnailName))
      })
      .on('error', (err) => {
        reject(err)
      })
      .screenshots({
        timestamps: [time],
        filename: thumbnailName,
        folder: outputPath,
        size: '320x240'
      })
  })
}
// 이미지 파일을 비율은 유지하면서 320x240 보다 작은 이미지 만들기
const resizeImage = (inputPath, outputPath) => {
  return new Promise((resolve, reject) => {
    ffmpeg(inputPath)
      .on('end', () => {
        resolve(outputPath)
      })
      .on('error', (err) => {
        reject(err)
      })
      .size(`min(320, 320)x240`)
      .save(outputPath)
  })
}

module.exports = {
  generateThumbnail,
  resizeImage
}
