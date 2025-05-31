const express = require('express')
const path = require('path')
const fs = require('fs')
const logger = require('@logger')
const multer = require('multer')
const { getLogoPath } = require('@api/files/folders')

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

router.get('/', (req, res) => {
  try {
    const files = fs.readdirSync(getLogoPath())
    res.json(files)
  } catch (error) {
    logger.error(`Error reading logo directory: ${error}`)
    res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.post('/', upload.any(), async (req, res) => {
  try {
    const files = req.files
    if (!files || files.length === 0) {
      return res.status(400).json({ error: 'No files uploaded' })
    }
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
  const { filename } = req.params
  const filePath = path.join(getLogoPath(), decodeURIComponent(filename))
  res.sendFile(filePath)
})

router.delete('/:filename', (req, res) => {
  const { filename } = req.params
  const filePath = path.join(getLogoPath(), decodeURIComponent(filename))

  fs.unlink(filePath, (err) => {
    if (err) {
      logger.error(`Error deleting logo file: ${err}`)
      return res.status(500).json({ error: 'Internal Server Error' })
    }
    res.json({ message: 'Logo file deleted successfully' })
  })
})

module.exports = router
