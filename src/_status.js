let pStatus = {
  windowOpen: false,
  activePlayerId: 0,
  playlistMode: false,
  playlistTrackIndex: 0,
  repeat: 'none',
  nics: [],
  tcpPort: 12345,
  udpPort: 12346,
  webPort: 3000,
  imageTime: 10,
  playlist: {},
  tracks: [],
  currentPlaylistId: null,
  startOnPlay: false,
  startOnPlaylist: '',
  device: {
    audiodevice: '',
    audiodevices: []
  },
  logo: {
    name: '',
    show: false,
    file: '',
    width: 0,
    height: 0,
    size: 0,
    x: 0,
    y: 0
  },
  player: [
    {
      event: '',
      buffering: 0,
      media_path: '',
      filename: '',
      volume: 100,
      speed: 1.0,
      duration: 0,
      time: 0,
      position: 0.0,
      fullscreen: false,
      playing: false,
      is_image: false,
      image_path: null,
      is_playing: 0
    },
    {
      event: '',
      buffering: 0,
      media_path: '',
      filename: '',
      volume: 100,
      speed: 1.0,
      duration: 0,
      time: 0,
      position: 0.0,
      fullscreen: false,
      playing: false,
      is_image: false,
      image_path: null,
      is_playing: 0
    }
  ],
  fullscreen: false,
  background: '#000000'
}

const updatePStatus = (newStatus) => {
  pStatus = { ...pStatus, ...newStatus }
}

let _pythonProcess = null

function getPythonProcess() {
  return _pythonProcess
}

function setPlayerProcess(proc) {
  _pythonProcess = proc
}

module.exports = {
  pStatus,
  updatePStatus,
  getPythonProcess,
  setPlayerProcess
}
