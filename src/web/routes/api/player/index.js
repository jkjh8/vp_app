const express = require('express')
const {
  playid,
  play,
  stop,
  pause,
  setFullscreen,
  setLogo,
  showLogo,
  setLogoSize,
  setBackground
} = require('@api/player/index.js')
const { pStatus } = require('@src/_status.js')
const { dbStatus } = require('@db')

const router = express.Router()

// id가 없을때는 그냥 플레이명령, id가 있으면 db에서 검색해서 파일위치를 함께 전송
router.get('/playid/:id', async (req, res) => {
  try {
    res.status(200).json({ message: await playid(req.params.id) })
  } catch (error) {
    console.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/play', async (req, res) => {
  try {
    res.status(200).send({ message: play() })
  } catch (error) {
    console.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/stop', async (req, res) => {
  try {
    res.status(200).json({ message: stop() })
  } catch (error) {
    console.error('Error occurred while stopping media:', error)
    res.status(500).send({ error: 'Failed to stop media' })
  }
})

router.get('/pause', async (req, res) => {
  try {
    res.status(200).json({ message: await pause() })
  } catch (error) {
    console.error('Error occurred while pausing media:', error)
    res.status(500).json({ error: 'Failed to pause media' })
  }
})

router.get('/fullscreen/:fullscreen', async (req, res) => {
  try {
    res
      .status(200)
      .json({ message: await setFullscreen(req.params.fullscreen === 'true') })
  } catch (error) {
    console.error('Error occurred while setting fullscreen mode:', error)
    res.status(500).json({ error: 'Failed to set fullscreen mode' })
  }
})

router.post('/background', async (req, res) => {
  try {
    res.status(200).json({ message: await setBackground(req.body.color) })
  } catch (error) {
    console.error('Error occurred while setting background color:', error)
    res.status(500).json({ error: 'Failed to set background color' })
  }
})

router.put('/setaudiodevice', async (req, res) => {
  try {
    const { deviceId } = req.body
    console.log('Setting audio device to:', deviceId)
    if (!deviceId) {
      return res.status(400).json({ error: 'Device ID is required' })
    }
    // Assuming there's a function to set the audio device
    // setAudioDevice(deviceId)
    require('@py').send({
      command: 'set_audio_device',
      device: deviceId
    })
    // db update
    console.log(
      await dbStatus.update(
        { type: 'audiodevice' },
        { $set: { audiodevice: deviceId } },
        { upsert: true }
      )
    )
    pStatus.device.audiodevice = deviceId
    res.status(200).json({ message: `Audio device set to ${deviceId}` })
  } catch (error) {
    console.error('Error occurred while setting audio device:', error)
    res.status(500).json({ error: 'Failed to set audio device' })
  }
})

module.exports = router
