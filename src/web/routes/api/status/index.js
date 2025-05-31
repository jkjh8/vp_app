const express = require('express')
const router = express.Router()
const { getSetupfromDB } = require('@src/api/status')
const db = require('@db')
const { pStatus } = require('@src/_status.js')
const logger = require('@logger')

router.use('/logo', require('./logo'))

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
    await db.status.update({ type: key }, { $set: { value } }, { upsert: true })
    logger.info(`Status updated for key "${key}" with value: ${value}`)
    // update player background if key is 'background'
    if (key === 'background') {
      require('@py').send({ command: 'background_color', color: value })
    }

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

module.exports = router
