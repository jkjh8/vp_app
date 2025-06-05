let pStatus = {
  activePlayerId: 0,
  playlistMode: false,
  playlistIndex: 0,
  repeat: 'none',
  nics: [],
  image_time: 10,
  current: {
    id: '',
    name: '',
    type: ''
  },
  playlistfile: '',
  playlist: {},
  tracks: [],
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
    x: 0,
    y: 0
  },
  player: {
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
    image_path: null
  },
  player1: {
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
    image_path: null
  },
  player2: {
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
    image_path: null
  },
  background: 'black'
}

let _pythonProcess = null

function getPythonProcess() {
  return _pythonProcess
}

function setPythonProcess(proc) {
  _pythonProcess = proc
}

module.exports = {
  pStatus,
  getPythonProcess,
  setPythonProcess
}
