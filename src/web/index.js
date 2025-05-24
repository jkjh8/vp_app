const path = require('path')
const express = require('express')
const cookieParser = require('cookie-parser')
const cors = require('cors')
const httpLogger = require('morgan')

const appServer = express()

// public 폴더 경로 정의
const publicFolder = path.join(__dirname, '../../public')

appServer.use(express.json())
appServer.use(express.urlencoded({ extended: true }))
appServer.use(cookieParser())
appServer.use(cors())
appServer.use(httpLogger('dev'))

if (process.env.NODE_ENV === 'development') {
  appServer.use(httpLogger('dev'))
}

appServer.use(express.static(path.join(publicFolder, 'spa')))
appServer.use('/', require('./routes'))

module.exports = appServer
