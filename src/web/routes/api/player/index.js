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
const router = express.Router()

// id가 없을때는 그냥 플레이명령, id가 있으면 db에서 검색해서 파일위치를 함께 전송
router.get('/playid/:id', async (req, res) => {
  try {
    const { id } = req.params
    playid(id)
    res.status(200).json({ message: `Playing file with ID: ${id}` })
  } catch (error) {
    console.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/play', async (req, res) => {
  try {
    play()
    res.status(200).send({ message: 'Media playback started successfully' })
  } catch (error) {
    console.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/stop', async (req, res) => {
  try {
    stop()
    res.status(200).json({ message: 'Media stopped successfully' })
  } catch (error) {
    console.error('Error occurred while stopping media:', error)
    res.status(500).send({ error: 'Failed to stop media' })
  }
})

router.get('/pause', async (req, res) => {
  try {
    pause() // Assuming stop is used for pause as well
    res.status(200).json({ message: 'Media paused successfully' })
  } catch (error) {
    console.error('Error occurred while pausing media:', error)
    res.status(500).json({ error: 'Failed to pause media' })
  }
})

router.get('/fullscreen/:fullscreen', async (req, res) => {
  try {
    const { fullscreen } = req.params
    setFullscreen(fullscreen === 'true')
    res.status(200).json({ message: 'Fullscreen mode set successfully' })
  } catch (error) {
    console.error('Error occurred while setting fullscreen mode:', error)
    res.status(500).json({ error: 'Failed to set fullscreen mode' })
  }
})

router.get('/logo/:logo', async (req, res) => {
  try {
    const { logo } = encodeURIComponent(req.params)
    setLogo(logo)
    res.status(200).json({ message: 'Logo set successfully' })
  } catch (error) {
    console.error('Error occurred while setting logo:', error)
    res.status(500).json({ error: 'Failed to set logo' })
  }
})

router.get('/show_logo/:show', async (req, res) => {
  try {
    const { show } = req.params
    showLogo(show === 'true')
    res.status(200).json({ message: 'Logo visibility set successfully' })
  } catch (error) {
    console.error('Error occurred while setting logo visibility:', error)
    res.status(500).json({ error: 'Failed to set logo visibility' })
  }
})

router.get('/logo_size/:height/:width', async (req, res) => {
  try {
    const { height, width } = req.params
    setLogoSize(Number(height), Number(width))
    res.status(200).json({ message: 'Logo size set successfully' })
  } catch (error) {
    console.error('Error occurred while setting logo size:', error)
    res.status(500).json({ error: 'Failed to set logo size' })
  }
})

router.get('/background/:color', async (req, res) => {
  try {
    const { color } = req.params
    setBackground(color)
    res.status(200).json({ message: 'Background color set successfully' })
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
    res.status(200).json({ message: `Audio device set to ${deviceId}` })
  } catch (error) {
    console.error('Error occurred while setting audio device:', error)
    res.status(500).json({ error: 'Failed to set audio device' })
  }
})

module.exports = router
