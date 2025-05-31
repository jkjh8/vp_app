const express = require('express')
const path = require('path')
const fs = require('fs')
const logger = require('@logger')
const multer = require('multer')
const { getLogoPath } = require('@api/files/folders')
const { pStatus } = require('../../../../../_status')
const db = require('@db')

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

router.get('/sel/:filename', async (req, res) => {
  try {
    const { filename } = req.params
    pStatus.logo.name = decodeURIComponent(filename)
    const filePath = path.join(getLogoPath(), pStatus.logo.name)
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Logo file not found' })
    }
    pStatus.logo.file = filePath
    // update db
    await db.status.update(
      { type: 'logo' },
      {
        $set: { file: pStatus.logo.file, name: pStatus.logo.name }
      },
      { upsert: true }
    )

    require('@py').send({
      command: 'logo',
      file: pStatus.logo.file
    })
    res.json({
      message: 'Logo file selected successfully',
      pStatus
    })
  } catch (error) {
    logger.error(`Error selecting logo file: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.get('/show/:show', (req, res) => {
  try {
    const { show } = req.params
    const showLogo = show === 'true'
    pStatus.logo.show = showLogo
    // update db
    db.status.update(
      { type: 'logo' },
      {
        $set: { show: pStatus.logo.show }
      },
      { upsert: true }
    )
    console.log(pStatus.logo.show)
    require('@py').send({
      command: 'show_logo',
      show: pStatus.logo.show
    })
    res.json({
      message: `Logo visibility set to ${showLogo}`,
      pStatus
    })
  } catch (error) {
    logger.error(`Error setting logo visibility: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

router.put('/size', async (req, res) => {
  try {
    const { width, height } = req.body
    if (typeof width !== 'number' || typeof height !== 'number') {
      return res.status(400).json({ error: 'Invalid width or height' })
    }
    pStatus.logo.width = width
    pStatus.logo.height = height

    // update db
    await db.status.update(
      { type: 'logo' },
      {
        $set: { width: pStatus.logo.width, height: pStatus.logo.height }
      },
      { upsert: true }
    )
    require('@py').send({
      command: 'logo_size',
      width: pStatus.logo.width,
      height: pStatus.logo.height
    })
    res.json({
      message: 'Logo size updated successfully',
      pStatus
    })
  } catch (error) {
    logger.error(`Error updating logo size: ${error}`)
    return res.status(500).json({ error: 'Internal Server Error' })
  }
})

module.exports = router
