const express = require('express')
const router = express.Router()

router.use('/files', require('./files'))
router.use('/player', require('./player'))
router.use('/status', require('./status'))

module.exports = router
