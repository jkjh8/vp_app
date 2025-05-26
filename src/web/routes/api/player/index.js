const express = require('express')
const { playid, play, stop, pause } = require('@api/player/index.js')
const router = express.Router()

// id가 없을때는 그냥 플레이명령, id가 있으면 db에서 검색해서 파일위치를 함께 전송
router.get('/playid/:id', async (req, res) => {
  try {
    const { id } = req.params
    const r = await playid(id)
    res.status(200).send(r)
  } catch (error) {
    console.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/play', async (req, res) => {
  try {
    const r = await play()
    res.status(200).send(r)
  } catch (error) {
    console.error('Error occurred while playing media:', error)
    res.status(500).send({ error: 'Failed to play media' })
  }
})

router.get('/stop', async (req, res) => {
  try {
    const r = await stop()
    res.status(200).send(r)
  } catch (error) {
    console.error('Error occurred while stopping media:', error)
    res.status(500).send({ error: 'Failed to stop media' })
  }
})

router.get('/pause', async (req, res) => {
  try {
    const r = await pause() // Assuming stop is used for pause as well
    res.status(200).json(r)
  } catch (error) {
    console.error('Error occurred while pausing media:', error)
    res.status(500).json({ error: 'Failed to pause media' })
  }
})

module.exports = router
