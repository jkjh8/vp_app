const express = require('express')
const router = express.Router()
const db = require('@db')
const { pStatus } = require('@src/_status.js')
const logger = require('@logger')

router.get('/', async (req, res) => {
  try {
    const playlists = await db.playlists.find()
    res.json(playlists)
  } catch (error) {
    logger.error('Error fetching playlists:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.post('/', async (req, res) => {
  const { name, description } = req.body
  if (!name) {
    return res.status(400).json({ error: 'Name is required' })
  }

  try {
    const newPlaylist = {
      name,
      description: description || '',
      tracks: []
    }

    const result = await db.playlists.insert(newPlaylist)
    logger.info(`Playlist "${name}" added successfully`)
    res.status(201).json(result)
  } catch (error) {
    logger.error('Error adding playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.put('/', async (req, res) => {
  const { id } = req.params
  const { name, description } = req.body

  if (!id) {
    return res.status(400).json({ error: 'Playlist ID is required' })
  }

  if (!name) {
    return res.status(400).json({ error: 'Name is required' })
  }

  try {
    const updateData = {
      name,
      description: description || ''
    }

    const numReplaced = await db.playlists.update(
      { _id: id },
      { $set: updateData },
      { returnUpdatedDocs: true }
    )

    if (numReplaced === 0) {
      return res.status(404).json({ error: 'Playlist not found' })
    }

    // 업데이트된 플레이리스트 조회
    const updatedPlaylist = await db.playlists.findOne({ _id: id })

    logger.info(`Playlist "${name}" with ID "${id}" updated successfully`)
    res.status(200).json(updatedPlaylist)
  } catch (error) {
    logger.error('Error updating playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

router.put('/tracks', async (req, res) => {
  const { id, tracks } = req.body
  if (!id || !Array.isArray(tracks)) {
    return res
      .status(400)
      .json({ error: 'Playlist ID and tracks are required' })
  }

  try {
    const updatedPlaylist = await db.playlists.update(
      { _id: id },
      { $set: { tracks } }
    )
    if (updatedPlaylist) {
      logger.info(`Tracks updated for playlist with ID "${id}"`)
      res.status(200).json(updatedPlaylist)
    } else {
      res.status(404).json({ error: 'Playlist not found' })
    }
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
    const result = await db.playlists.remove({ _id: id })
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

module.exports = router
