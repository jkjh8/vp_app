const express = require('express')
const {
  playid,
  play,
  stop,
  pause,
  setFullscreen,
  setBackground,
  setAudioDevice,
  setRepeat,
  setNext,
  setPrevious
} = require('@api/player/index.js')
const { pStatus } = require('@src/_status.js')
const { dbStatus } = require('@db')
const logger = require('@logger')

const router = express.Router()

// id가 없을때는 그냥 플레이명령, id가 있으면 db에서 검색해서 파일위치를 함께 전송
router.get('/playid/:id', async (req, res) => {
  try {
    res.status(200).json({ message: await playid(Number(req.params.id)) })
  } catch (error) {
    logger.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/play/:id', async (req, res) => {
  try {
    res.status(200).send({ message: play(Number(req.params.id)) })
  } catch (error) {
    logger.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/stop', async (req, res) => {
  try {
    res.status(200).json({ message: stop() })
  } catch (error) {
    logger.error('Error occurred while stopping media:', error)
    res.status(500).send({ error: 'Failed to stop media' })
  }
})

router.get('/pause/:id', async (req, res) => {
  try {
    res.status(200).json({ message: await pause(Number(req.params.id)) })
  } catch (error) {
    logger.error('Error occurred while pausing media:', error)
    res.status(500).json({ error: 'Failed to pause media' })
  }
})

router.get('/fullscreen/:value', async (req, res) => {
  try {
    res
      .status(200)
      .json({ message: await setFullscreen(req.params.value === 'true') })
  } catch (error) {
    logger.error('Error occurred while setting fullscreen mode:', error)
    res.status(500).json({ error: 'Failed to set fullscreen mode' })
  }
})

router.post('/background', async (req, res) => {
  try {
    res.status(200).json({ message: await setBackground(req.body.color) })
  } catch (error) {
    logger.error('Error occurred while setting background color:', error)
    res.status(500).json({ error: 'Failed to set background color' })
  }
})

router.put('/setaudiodevice', async (req, res) => {
  try {
    res.status(200).json({ message: await setAudioDevice(req.body.deviceId) })
  } catch (error) {
    logger.error('Error occurred while setting audio device:', error)
    res.status(500).json({ error: 'Failed to set audio device' })
  }
})

router.get('/repeat', async (req, res) => {
  try {
    const r = await setRepeat()
    res.status(200).json({ message: `Repeat mode set to: ${r}`, mode: r })
  } catch (error) {
    logger.error('Error occurred while setting repeat mode:', error)
    res.status(500).json({ error: 'Failed to set repeat mode' })
  }
})

router.get('/next', async (req, res) => {
  try {
    res.status(200).json({ message: await setNext() })
  } catch (error) {
    logger.error('Error occurred while setting next track: ' + error)
    res.status(500).json({ error: 'Failed to set next track' })
  }
})

router.get('/prev', async (req, res) => {
  try {
    res.status(200).json({ message: await setPrevious() })
  } catch (error) {
    logger.error('Error occurred while setting previous track:' + error)
    res.status(500).json({ error: 'Failed to set previous track' })
  }
})

module.exports = router
