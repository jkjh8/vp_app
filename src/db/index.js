const path = require('path')
const Datastore = require('nedb-promises')

const addTimestamps = (store) => {
  // Insert 시 timestamps 추가
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

  // Update 시 updatedAt 추가
  const originalUpdate = store.update
  store.update = function (query, update, options) {
    if (!update.$set) {
      update.$set = {}
    }
    update.$set.updatedAt = new Date()
    return originalUpdate.call(this, query, update, options)
  }

  return store
}

let db = null

const initDb = (dbPath) => {
  if (db) {
    return db
  }
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

// Status 함수들
const dbStatus = {
  async find(query = {}) {
    const { db } = require('./index')
    return await db.status.find(query)
  },
  async findOne(query = {}) {
    const { db } = require('./index')
    return await db.status.findOne(query)
  },
  async insert(doc) {
    const { db } = require('./index')
    return await db.status.insert(doc)
  },
  async update(query, update, options = {}) {
    const { db } = require('./index')
    return await db.status.update(
      query,
      { $set: update },
      { ...options, upsert: true }
    )
  },
  async remove(query, options = {}) {
    const { db } = require('./index')
    return await db.status.remove(query, options)
  }
}

// Files 함수들
const dbFiles = {
  async find(query = {}) {
    const { db } = require('./index')
    return await db.files.find(query)
  },
  async findOne(query = {}) {
    const { db } = require('./index')
    return await db.files.findOne(query)
  },
  async insert(doc) {
    const { db } = require('./index')
    return await db.files.insert(doc)
  },
  async update(query, update, options = {}) {
    const { db } = require('./index')
    return await db.files.update(
      query,
      { $set: update },
      { ...options, upsert: true }
    )
  },
  async remove(query, options = {}) {
    const { db } = require('./index')
    return await db.files.remove(query, options)
  }
}

// Playlists 함수들
const dbPlaylists = {
  async find(query = {}) {
    const { db } = require('./index')
    return await db.playlists.find(query)
  },
  async findOne(query = {}) {
    const { db } = require('./index')
    return await db.playlists.findOne(query)
  },
  async insert(doc) {
    const { db } = require('./index')
    return await db.playlists.insert(doc)
  },
  async update(query, update, options = {}) {
    const { db } = require('./index')
    return await db.playlists.update(
      query,
      { $set: update },
      {
        ...options,
        upsert: true
      }
    )
  },
  async remove(query, options = {}) {
    const { db } = require('./index')
    return await db.playlists.remove(query, options)
  }
}

module.exports = {
  initDb,
  get db() {
    return db
  },
  dbStatus,
  dbFiles,
  dbPlaylists
}
