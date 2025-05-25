const express = require('express')
const multer = require('multer')
const logger = require('@logger')
const { postProcessFiles } = require('@api/files')
const path = require('path')
const fs = require('fs')
const db = require('@db')
const { getTmpPath, getMediaPath } = require('@api/files/folders')
const router = express.Router()

const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      const tmpPath = getTmpPath()
      console.log('tmpPath:', tmpPath)
      cb(null, tmpPath)
    },
    filename: (req, file, cb) => {
      cb(null, decodeURIComponent(file.fieldname))
    }
  })
})

// 파일 목록 조회
router.get('/', async (req, res) => {
  try {
    const files = await db.files.find({})
    res.json(files)
  } catch (error) {
    logger.error(`Error fetching files: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

// 파일 업로드. 업로드 하면 일단 임시폴더에 저장하고 uuid를 지정하고 미디어 폴더에 uuid폴더 생성후 저장. 저장시 db에 uuid와 경로 정보, 메타데이터 포함 저장. 저장시 비디오 파일은 썸네일 생성 및 저장. 이미지 파일이면 작은 이미지로 변환 후 저장. 오디오 파일은 썸네일 생략
router.post('/', upload.any(), async (req, res) => {
  try {
    const files = req.files
    if (!files || files.length === 0) {
      return res.status(400).json({ error: 'No files uploaded' })
    }
    // Process the uploaded files
    await postProcessFiles(files)
    return res
      .status(200)
      .json({ message: 'Files processed successfully', files })
  } catch (error) {
    logger.error(`Error processing files: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

// 섬네일 파일을 요청하면 보내주기
router.get('/thumbnail/:uuid', async (req, res) => {
  const { uuid } = req.params
  try {
    const file = await db.files.findOne({ uuid })
    if (!file) {
      return res.status(404).json({ error: 'File not found' })
    }
    const thumbnailPath = file.thumbnail // Assuming thumbnailPath is stored in the database
    res.sendFile(thumbnailPath)
  } catch (error) {
    logger.error(`Error fetching thumbnail: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

// 파일 삭제
router.delete('/:uuid', async (req, res) => {
  const { uuid } = req.params
  try {
    const file = await db.files.findOne({ uuid })
    if (!file) {
      return res.status(404).json({ error: 'File not found' })
    }
    // Delete the uuid folder from the filesystem
    const fileDir = path.join(getMediaPath(), uuid)
    fs.rmdirSync(fileDir, { recursive: true, force: true }) // This will delete the directory and its contents
    // Delete the file record from the database
    await db.files.remove({ uuid })

    res.status(200).json({ message: 'File deleted successfully' })
  } catch (error) {
    logger.error(`Error deleting file: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

module.exports = router
