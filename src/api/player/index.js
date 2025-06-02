const path = require('path')
const logger = require('@logger')
const { pStatus } = require('@src/_status')
const { dbStatus, dbFiles } = require('@db')
const { getLogoPath } = require('@api/files/folders')

const playid = async (id) => {
  logger.info(`Received play request with ID: ${id}`)
  const file = await dbFiles.findOne({ number: Number(id) })
  if (!file) {
    throw new Error('Player not found')
  }
  pStatus.current = file
  require('@py').send({ command: 'playid', file: file })
  return `Playing file: ${file.path}`
}

const play = () => {
  logger.info('Received play request without ID')
  require('@py').send({ command: 'play' })
  return 'Playing without ID'
}

const pause = () => {
  logger.info('Received pause request')
  require('@py').send({ command: 'pause' })
  return 'Player paused'
}

const stop = () => {
  logger.info('Received stop request')
  require('@py').send({ command: 'stop' })
  return 'Player stopped'
}

const updateTime = (time) => {
  logger.info(`Updating player time to: ${time}`)
  require('@py').send({ command: 'time', time })
}

const setFullscreen = async (fullscreen) => {
  logger.info(`Setting fullscreen mode to: ${fullscreen}`)
  await dbStatus.update(
    { type: 'fullscreen' },
    { $set: { fullscreen } },
    { upsert: true }
  )
  require('@py').send({ command: 'fullscreen', fullscreen })
}

const setLogo = async (logo) => {
  logger.info(`Setting logo to: ${logo}`)
  const filePath = path.join(getLogoPath(), logo)

  pStatus.logo.name = logo
  pStatus.logo.file = filePath
  await dbStatus.update(
    { type: 'logo' },
    { $set: { file: filePath, name: logo } },
    { upsert: true }
  )
  require('@py').send({ command: 'logo', file: filePath })
  return `Logo set to: ${logo}`
}

const showLogo = async (show) => {
  logger.info(`Setting logo visibility to: ${show}`)
  pStatus.logo.show = show
  await dbStatus.update({ type: 'logo' }, { $set: { show } }, { upsert: true })
  require('@py').send({ command: 'show_logo', show })
  return `Logo visibility set to: ${show}`
}

const setLogoSize = async (h, w) => {
  logger.info(`Setting logo size to: height=${h}, width=${w}`)
  pStatus.logo.height = h
  pStatus.logo.width = w
  await dbStatus.update(
    { type: 'logo' },
    { $set: { height: h, width: w } },
    { upsert: true }
  )
  require('@py').send({
    command: 'logo_size',
    height: h,
    width: w
  })
  return `Logo size set to: height=${h}, width=${w}`
}

const setBackground = async (background) => {
  logger.info(`Setting background to: ${background}`)
  require('@py').send({
    command: 'background_color',
    color: background
  })
  pStatus.background = background
  await dbStatus.update(
    { type: 'background' },
    { $set: { value: background } },
    { upsert: true }
  )
  return `Background set to: ${background}`
}

const setImageTime = async (time) => {
  logger.info(`Setting image time to: ${time}`)
  require('@py').send({
    command: 'image_time',
    time
  })
}

module.exports = {
  playid,
  play,
  stop,
  pause,
  updateTime,
  setFullscreen,
  setLogo,
  showLogo,
  setLogoSize,
  setBackground,
  setImageTime
}
