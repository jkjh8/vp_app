const { app } = require('electron')
const path = require('path')
const Datastore = require('nedb-promises')

const dbPath = path.join(__dirname, 'db')

const db = {
  status: Datastore.create({
    filename: path.join(dbPath, 'status.db'),
    autoload: true
  }),
  files: Datastore.create({
    filename: path.join(dbPath, 'files.db'),
    autoload: true
  }),
  playlists: Datastore.create({
    filename: path.join(dbPath, 'playlists.db'),
    autoload: true
  })
}

module.exports = db
