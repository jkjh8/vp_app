const { pStatus } = require('../../_status')
const { dbPlaylists, dbFiles } = require('../../db')
const {
  sendPlayerCommand,
  sendMessageToClient,
  broadcastTcpMessage
} = require('../../api')
const logger = require('../../logger')

const getTracksWithFileInfo = async (tracks) => {
  if (!tracks || tracks.length === 0) return []
  return await Promise.all(
    tracks.map(async (track) => {
      const file = await dbFiles.findOne({ uuid: track.uuid })
      if (file) {
        return {
          filename: file.filename,
          path: file.path,
          uuid: file.uuid,
          mimetype: file.mimetype,
          is_image: file.is_image,
          time: track.time || 0,
          amx: file.amx || null
        }
      }
    })
  )
}

const getPlaylist = async (playlistId) => {
  if (!playlistId) {
    throw new Error('Playlist ID is required')
  }
  const playlist = await dbPlaylists.findOne({ playlistId })
  if (!playlist) {
    throw new Error('Playlist not found')
  }
  return await getTracksWithFileInfo(playlist.tracks)
}

const fnGetPlaylists = async () => {
  try {
    let playlists = await dbPlaylists.find()
    for (const playlist of playlists) {
      playlist.tracks = await getTracksWithFileInfo(playlist.tracks)
    }
    return playlists
  } catch (error) {
    console.error('Error fetching playlists:', error)
    throw error
  }
}

const fnAddPlaylists = async (args) => {
  if (!args.playlistId) return new Error('playlistId is required')
  return await dbPlaylists.insert({ ...args, tracks: [] })
}

const fnEditPlaylists = async (args) => {
  const { id, ...updateData } = args
  if (!id) return new Error('Playlist ID is required')
  return await dbPlaylists.update({ _id: id }, { $set: updateData })
}

const fnAddTracksToPlaylist = async (playlistId, tracks) => {
  if (!playlistId || !Array.isArray(tracks)) {
    throw new Error('Playlist ID and tracks are required')
  }
  return await dbPlaylists.update(
    { _id: playlistId },
    { $addToSet: { tracks: { $each: tracks } } }
  )
}

const setPlaylist = async (playlistId) => {
  return new Promise(async (resolve, reject) => {
    if (!playlistId) {
      return reject(new Error('Playlist ID is required'))
    }
    const playlist = await dbPlaylists.findOne({ playlistId })
    if (!playlist) {
      return reject(new Error('Playlist not found'))
    }
    pStatus.playlist = playlist || {}
    pStatus.currentPlaylistId = playlistId
    pStatus.tracks = playlist.tracks || []
    playlist.tracks = await getTracksWithFileInfo(playlist.tracks)
    sendPlayerCommand('set_tracks', {
      tracks: playlist.tracks
    })
    sendMessageToClient('pStatus', {
      playlist: pStatus.playlist,
      currentPlaylistId: pStatus.currentPlaylistId,
      tracks: pStatus.tracks
    })

    broadcastTcpMessage(
      `set_playlist,${playlistId},${playlist.name},${playlist.tracks.length}`
    )
    resolve(`Playlist set to: ${playlist.name}`)
  })
}

const setplaylistTrackIndex = async (index) => {
  if (index === undefined || index === null) {
    throw new Error('Index is required')
  }
  if (typeof index !== 'number') {
    throw new Error('Index must be a number')
  }
  sendPlayerCommand('playlist_track_index', { index })
  return `Playlist index set to: ${index}`
}

const setPlaylistMode = async (mode) => {
  return new Promise((resolve, reject) => {
    sendPlayerCommand('playlist_mode', { value: mode })
    pStatus.playlistMode = mode
    sendMessageToClient('pStatus', { playlistMode: mode })
    resolve(`Playlist mode set to: ${mode}`)
  })
}

const editImageRenderTime = async (playlistId, idx, time) => {
  if (!playlistId || idx === undefined || time === undefined) {
    throw new Error('Playlist ID, track index, and time are required')
  }
  // playlist _id를 찾아서 tracks의 idx번째 track의 time값을 수정
  const playlist = await dbPlaylists.findOne({ _id: playlistId })
  if (!playlist) {
    throw new Error('Playlist not found')
  }
  if (!playlist.tracks || !playlist.tracks[idx]) {
    throw new Error('Track not found in playlist')
  }
  playlist.tracks[idx].time = time
  await dbPlaylists.update(
    { _id: playlistId },
    { $set: { tracks: playlist.tracks } }
  )
  sendPlayerCommand('set_tracks', {
    tracks: playlist.tracks
  })
}

const playlistPlay = async (playlistId, trackIndex) => {
  logger.warn('playlistPlay called with:' + playlistId + ' ' + trackIndex)
  if (!playlistId) {
    return 'Playlist ID is required'
  }

  if ((await dbPlaylists.findOne({ playlistId })) === null) {
    return 'Playlist not found'
  }

  logger.info(await setPlaylist(playlistId))
  logger.info(await setPlaylistMode(true))

  pStatus.currentPlaylistId = playlistId
  pStatus.playlistTrackIndex = trackIndex

  sendPlayerCommand('playlist_play', {
    idx: trackIndex
  })

  require('../../tcp').broadcastTcpMessage(
    `playlist,${playlistId},${trackIndex}`
  )
  return null
}

module.exports = {
  fnGetPlaylists,
  getPlaylist,
  fnAddPlaylists,
  fnEditPlaylists,
  fnAddTracksToPlaylist,
  setPlaylist,
  setPlaylistMode,
  setplaylistTrackIndex,
  playlistPlay,
  editImageRenderTime
}
