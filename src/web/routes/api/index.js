const express = require('express')
const router = express.Router()

router.use('/files', require('./files'))
router.use('/player', require('./player'))

module.exports = router
