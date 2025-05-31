let pStatus = {
  playlistmode: false,
  playlistindex: 0,
  repeat: 'none',
  nics: [],
  darkmode: false,
  current: {
    id: '',
    name: '',
    type: ''
  },
  playlistfile: '',
  playlist: [],
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
