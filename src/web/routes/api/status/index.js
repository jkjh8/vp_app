const express = require('express')
const router = express.Router()
const { getSetupfromDB } = require('@src/api/status')
const { pStatus } = require('@src/_status.js')
const logger = require('@logger')
const { dbStatus } = require('@db')

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
    await dbStatus.update({ type: key }, { $set: { value } }, { upsert: true })
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

router.get('/image_time/:time', async (req, res) => {
  const { time } = req.params
  if (!time) {
    return res.status(400).json({ error: 'Time parameter is required' })
  }

  try {
    // Fetch the image for the given time
    const image = await dbStatus.findOne({ type: 'image_time', time })
    if (!image) {
      return res
        .status(404)
        .json({ error: 'Image not found for the specified time' })
    }
    pStatus.image_time = image.value
    require('@py').send({ command: 'image_time', time })

    res.json({
      success: true,
      message: `Image fetched for time "${time}"`,
      pStatus
    })
  } catch (error) {
    logger.error(`Error fetching image for time "${time}":`, error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

module.exports = router
