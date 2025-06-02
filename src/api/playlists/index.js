const { pStatus } = require('../../_status')
const { dbPlaylists, dbFiles } = require('@db')

const fnGetPlaylists = async () => {
  try {
    let playlists = await dbPlaylists.find()
    // playlists의 각 항목의 tracks 필드에서 uuid를 files에서 조회해서 대체하기
    for (const playlist of playlists) {
      if (playlist.tracks && playlist.tracks.length > 0) {
        playlist.tracks = await Promise.all(
          playlist.tracks.map(async (track) => {
            const file = await dbFiles.findOne({ uuid: track })
            if (file) {
              return file
            }
          })
        )
      } else {
        playlist.tracks = []
      }
    }
    // pStatus에 직접 저장 (value 없이)
    pStatus.playlists = playlists
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

module.exports = {
  fnGetPlaylists,
  fnAddPlaylists,
  fnEditPlaylists,
  fnAddTracksToPlaylist
}
