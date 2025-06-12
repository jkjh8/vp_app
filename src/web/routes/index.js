const express = require('express')
const router = express.Router()
const path = require('path')
const logger = require('../../logger')

router.get('/', (req, res) => {
  try {
    res.sendFile(path.join(__dirname, '../../public/spa/index.html'))
  } catch (error) {
    logger.error('Error serving index.html:', error)
    res.status(500).send('Internal Server Error')
  }
})

router.use('/api/files', require('./files'))
router.use('/api/player', require('./player'))
router.use('/api/status', require('./status'))
router.use('/api/playlist', require('./playlist'))

module.exports = router
