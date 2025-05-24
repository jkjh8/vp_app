const express = require('express')
const router = express.Router()

router.get('/', (req, res) => {
  res.send('Welcome to the API')
})

router.use('/api', require('./api'))
module.exports = router
