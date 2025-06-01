const express = require('express')
const router = express.Router()
const path = require('path')
const logger = require('@logger')

// Serve static files from the 'public/spa' directory
router.use(express.static(path.join(__dirname, '../../public/spa')))

router.get('/', (req, res) => {
  try {
    res.sendFile(path.join(__dirname, '../../public/spa/index.html'))
  } catch (error) {
    logger.error('Error serving index.html:', error)
    res.status(500).send('Internal Server Error')
  }
})

router.use('/api', require('./api'))
module.exports = router
