const express = require('express')
const router = express.Router()
const db = require('../../../../db')
const { pStatus } = require('../../../../_status.js')
const { dbPlaylists } = require('../../../../db')
const logger = require('../../../../logger')

const {
  fnGetPlaylists,
  fnAddPlaylists,
  fnEditPlaylists,
  fnAddTracksToPlaylist,
  playlistPlay
} = require('../../../../api/playlists')

router.get('/', async (req, res) => {
  try {
    const playlists = await fnGetPlaylists()
    // playlists를 pStatus에 저장
    res.json(playlists)
  } catch (error) {
    logger.error('Error fetching playlists:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.post('/', async (req, res) => {
  try {
    const r = await fnAddPlaylists(req.body)
    logger.info(`Playlist "${r}" added successfully`)
    res.status(201).json(r)
  } catch (error) {
    logger.error('Error adding playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.put('/', async (req, res) => {
  try {
    const r = await fnEditPlaylists(req.body)
    logger.info(`Playlist "${r}" updated successfully`)
    res.status(200).json(r)
  } catch (error) {
    logger.error('Error updating playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.put('/tracks', async (req, res) => {
  const { id, tracks } = req.body
  try {
    const r = await fnAddTracksToPlaylist(id, tracks)
    logger.info(`Tracks added to playlist "${id}" successfully`)
    res.status(200).json(r)
  } catch (error) {
    logger.error('Error updating playlist tracks:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.delete('/:id', async (req, res) => {
  const { id } = req.params
  if (!id) {
    return res.status(400).json({ error: 'Playlist ID is required' })
  }

  try {
    const result = await dbPlaylists.remove({ _id: id })
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Playlist not found' })
    } else {
      logger.info(`Playlist with ID "${id}" deleted successfully`)
      res.status(200).json({ message: 'Playlist deleted successfully' })
    }
  } catch (error) {
    logger.error('Error deleting playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.get('/play', async (req, res) => {
  const { playlistId, trackIndex } = req.query
  try {
    const result = await playlistPlay(Number(playlistId), Number(trackIndex))
    res.status(200).json(result)
  } catch (error) {
    logger.error('Error playing from playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

module.exports = router
