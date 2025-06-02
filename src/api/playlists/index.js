const { pStatus } = require('../../_status')
const db = require('@db')

const fnGetPlaylists = async (req, res) => {
  try {
    let playlists = await db.playlists.find()
    // playlists의 각 항목의 tracks 필드에서 uuid를 files에서 조회해서 대체하기
    for (const playlist of playlists) {
      if (playlist.tracks && playlist.tracks.length > 0) {
        playlist.tracks = await Promise.all(
          playlist.tracks.map(async (track) => {
            const file = await db.files.findOne({ uuid: track })
            if (file) {
              return file
            }
          })
        )
      } else {
        playlist.tracks = []
      }
    }
    // playlists를 pStatus에 저장
    pStatus.value.playlists = playlists
    return playlists
  } catch (error) {
    console.error('Error fetching playlists:', error)
    throw error
  }
}

module.exports = {
  fnGetPlaylists
}
