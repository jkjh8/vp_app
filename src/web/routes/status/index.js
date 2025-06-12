const express = require('express')
const router = express.Router()
const { getSetupfromDB } = require('../../../api/status/index.js')
const { pStatus } = require('../../../_status.js')
const logger = require('../../../logger/index.js')
const { dbStatus } = require('../../../db/index.js')
const { setImageTime } = require('../../../api/player/index.js')

router.use('/logo', require('./logo/index.js'))

router.get('/', async (req, res) => {
  try {
    res.json(await getSetupfromDB())
  } catch (error) {
    logger.error('Error fetching setup:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.post('/update', async (req, res) => {
  const { key, value } = req.body
  if (!key || value === undefined) {
    return res.status(400).json({ error: 'Key and value are required' })
  }

  try {
    // Update the pStatus object
    pStatus[key] = value

    // Save the updated status to the database
    await dbStatus.update({ type: key }, { value })
    logger.info(`Status updated for key "${key}" with value: ${value}`)

    res.json({
      success: true,
      message: `Status updated for key "${key}"`,
      pStatus
    })
  } catch (error) {
    logger.error(`Error updating status for key "${key}":`, error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.get('/image_time/:time', async (req, res) => {
  try {
    res.json({
      success: true,
      message: await setImageTime(Number(req.params.time)),
      pStatus
    })
  } catch (error) {
    logger.error(`Error fetching image for time "${req.params.time}":`, error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

module.exports = router
