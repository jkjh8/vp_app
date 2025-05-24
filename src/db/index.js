const { app } = require('electron')
const path = require('path')
const Datastore = require('nedb-promises')
const logger = require('@logger')

let dbStatus = null
let dbFiles = null
let dbPlaylists = null

const dbPath = path.resolve(app.getPath('appData'), 'vp', 'db')
const dbStatusPath = path.join(dbPath, 'status.json')
const dbFilePath = path.join(dbPath, 'db.json')
const dbPlaylistsPath = path.join(dbPath, 'playlists.json')

const dbInit = () => {
  try {
    dbStatus = Datastore.create({ filename: dbStatusPath, autoload: true })
    dbFiles = Datastore.create({ filename: dbFilePath, autoload: true })
    dbPlaylists = Datastore.create({
      filename: dbPlaylistsPath,
      autoload: true
    })
  } catch (error) {
    logger.error('Failed to initialize database:', error)
  }
}

module.exports = {
  dbInit,
  dbStatus,
  dbFiles,
  dbPlaylists
}
