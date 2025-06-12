const path = require('path')
const Datastore = require('nedb-promises')

// 네드비에 createdAt, updatedAt 자동 추가
const addTimestamps = (store) => {
  const originalInsert = store.insert
  store.insert = function (doc) {
    const now = new Date()
    if (Array.isArray(doc)) {
      doc.forEach((d) => {
        d.createdAt = now
        d.updatedAt = now
      })
    } else {
      doc.createdAt = now
      doc.updatedAt = now
    }
    return originalInsert.call(this, doc)
  }

  const originalUpdate = store.update
  store.update = function (query, update, options) {
    if (!update.$set) update.$set = {}
    update.$set.updatedAt = new Date()
    return originalUpdate.call(this, query, update, options)
  }
  return store
}

let db = null

const initDb = (dbPath) => {
  if (db) return db
  const dbDir = path.join(dbPath, 'db')
  db = {
    status: addTimestamps(
      Datastore.create({
        filename: path.join(dbDir, 'status.db'),
        autoload: true
      })
    ),
    files: addTimestamps(
      Datastore.create({
        filename: path.join(dbDir, 'files.db'),
        autoload: true
      })
    ),
    playlists: addTimestamps(
      Datastore.create({
        filename: path.join(dbDir, 'playlists.db'),
        autoload: true
      })
    )
  }
  return db
}

// 공통 CRUD 래퍼 생성 함수
const makeDbApi = (table) => ({
  async find(query = {}) {
    return db[table].find(query)
  },
  async findOne(query = {}) {
    return db[table].findOne(query)
  },
  async insert(doc) {
    return db[table].insert(doc)
  },
  async update(query, update, options = {}) {
    const { db } = require('./index')
    // update 객체에 $set이 이미 있으면 그대로, 아니면 감싸서 넘김
    const updateObj =
      update && Object.keys(update).some((k) => k.startsWith('$'))
        ? update
        : { $set: update }
    return db[table].update(query, updateObj, { ...options, upsert: true })
  },
  async remove(query, options = {}) {
    return db[table].remove(query, options)
  }
})

const dbStatus = makeDbApi('status')
const dbFiles = makeDbApi('files')
const dbPlaylists = makeDbApi('playlists')

module.exports = {
  initDb,
  get db() {
    return db
  },
  dbStatus,
  dbFiles,
  dbPlaylists
}
