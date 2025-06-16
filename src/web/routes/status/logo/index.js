const express = require('express')
const path = require('path')
const fs = require('fs')
const logger = require('@logger/index.js')
const multer = require('multer')
const { getLogoPath } = require('@api/files/folders.js')
const { pStatus } = require('@/_status.js')
const { dbStatus } = require('@db/index.js')
const { setLogo, showLogo, setLogoSize } = require('@api/player/index.js')
const sharp = require('sharp')

const router = express.Router()
const upload = multer({
  storage: multer.diskStorage({
    destination: (req, file, cb) => {
      cb(null, getLogoPath())
    },
    filename: (req, file, cb) => {
      cb(null, decodeURIComponent(file.fieldname))
    }
  })
})

router.get('/', async (req, res) => {
  try {
    res.json(await fs.promises.readdir(getLogoPath()))
  } catch (error) {
    logger.error(`Error reading logo directory: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.post('/', upload.any(), async (req, res) => {
  try {
    const files = req.files
    // svg파일이면 png로 변환
    // for (const file of files) {
    //   if (path.extname(file.filename).toLowerCase() === '.svg') {
    //     const pngPath = file.path.replace(/\.svg$/i, '.png')
    //     await sharp(file.path).png().toFile(pngPath)
    //     // 필요하다면 DB에 pngPath 저장 등 추가 작업
    //     // 원본 SVG 삭제 (선택)
    //     fs.unlinkSync(file.path)
    //     file.convertedPng = pngPath
    //   }
    // }

    res.status(200).json({
      message: 'Logo file uploaded successfully',
      files: files
    })
  } catch (error) {
    logger.error(`Error uploading logo file: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.get('/img/:filename', (req, res) => {
  try {
    const { filename } = req.params
    const filePath = path.join(getLogoPath(), decodeURIComponent(filename))
    res.sendFile(filePath)
  } catch (error) {
    logger.error(`Error fetching logo image: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.delete('/:filename', async (req, res) => {
  const { filename } = req.params
  const filePath = path.join(getLogoPath(), decodeURIComponent(filename))
  // 파일을 지울때 pStatus.logo.file == filename 이면 pStatus.logo.file = ''
  if (pStatus.logo.file === decodeURIComponent(filename)) {
    pStatus.logo.file = ''
    //db에서도 삭제
    await dbStatus.update({ type: 'logo' }, { $set: { file: '' } })
  }

  fs.unlink(filePath, (err) => {
    if (err) {
      logger.error(`Error deleting logo file: ${err}`)
      return res.status(500).json({ error: 'Internal Server Error' })
    }
    res.json({ message: 'Logo file deleted successfully' })
  })
})

router.get('/sel/:filename', async (req, res) => {
  try {
    res.json({
      message: await setLogo(decodeURIComponent(req.params.filename)),
      pStatus
    })
  } catch (error) {
    logger.error(`Error selecting logo file: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.get('/show/:show', async (req, res) => {
  try {
    res.json({
      message: await showLogo(req.params.show === 'true'),
      pStatus
    })
  } catch (error) {
    logger.error(`Error setting logo visibility: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.put('/size', async (req, res) => {
  try {
    res.json({
      message: await setLogoSize(req.body.size),
      pStatus
    })
  } catch (error) {
    logger.error(`Error updating logo size: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

module.exports = router
