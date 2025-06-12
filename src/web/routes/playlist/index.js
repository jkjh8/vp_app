const express = require('express')
const router = express.Router()
const { dbPlaylists } = require('../../../db')
const logger = require('../../../logger')
const {
  fnGetPlaylists,
  fnAddPlaylists,
  fnEditPlaylists,
  fnAddTracksToPlaylist,
  playlistPlay,
  editImageRenderTime
} = require('../../../api/playlists')

// 전체 플레이리스트 조회
router.get('/', async (req, res) => {
  try {
    const playlists = await fnGetPlaylists()
    res.json(playlists)
  } catch (error) {
    logger.error('Error fetching playlists:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

// 플레이리스트 추가
router.post('/', async (req, res) => {
  try {
    const result = await fnAddPlaylists(req.body)
    logger.info(`Playlist "${result}" added successfully`)
    res.status(201).json(result)
  } catch (error) {
    logger.error('Error adding playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

// 플레이리스트 수정
router.put('/', async (req, res) => {
  try {
    const result = await fnEditPlaylists(req.body)
    logger.info(`Playlist "${result}" updated successfully`)
    res.status(200).json(result)
  } catch (error) {
    logger.error('Error updating playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

// 트랙 추가
router.put('/tracks', async (req, res) => {
  const { id, tracks } = req.body
  try {
    const result = await fnAddTracksToPlaylist(id, tracks)
    logger.info(`Tracks added to playlist "${id}" successfully`)
    res.status(200).json(result)
  } catch (error) {
    logger.error('Error updating playlist tracks:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

// 플레이리스트 삭제
router.delete('/:id', async (req, res) => {
  const { id } = req.params
  if (!id) {
    return res.status(400).json({ error: 'Playlist ID is required' })
  }
  try {
    const result = await dbPlaylists.remove({ _id: id })
    if (result.deletedCount === 0) {
      return res.status(404).json({ error: 'Playlist not found' })
    }
    logger.info(`Playlist with ID "${id}" deleted successfully`)
    res.status(200).json({ message: 'Playlist deleted successfully' })
  } catch (error) {
    logger.error('Error deleting playlist:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

// 플레이리스트 재생
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

// 이미지 송출 시간 설정
router.put('/image_time', async (req, res) => {
  const { playlistId, idx, time } = req.body
  try {
    const result = await editImageRenderTime(playlistId, idx, time)
    logger.info(
      `Image render time for playlist "${playlistId}" updated successfully`
    )
    res.status(200).json(result)
  } catch (error) {
    logger.error('Error updating image render time:', error)
    res.status(500).json({ error: 'Internal Server Error, ' + error.message })
  }
})

module.exports = router
