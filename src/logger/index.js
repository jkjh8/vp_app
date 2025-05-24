// wiston logger
const winston = require('winston')
const DailyRotateFile = require('winston-daily-rotate-file')
const { app } = require('electron')
const path = require('path')

const { combine, timestamp, printf, colorize } = winston.format
const logDir = path.join(app.getPath('appData'), 'eventlog')

winston.addColors({
  error: 'red',
  warn: 'yellow',
  info: 'green',
  debug: 'blue'
})

const logger = winston.createLogger({
  level: 'info',
  levels: {
    error: 0,
    warn: 1,
    info: 2,
    debug: 3
  },
  format: combine(
    timestamp({
      format: 'YYYY-MM-DD HH:mm:ss'
    }),
    printf(function ({ timestamp, level, message, stack }) {
      return timestamp + ' [' + level + ']: ' + message + ' ' + (stack || '')
    })
  ),
  transports: [
    new winston.transports.Console({
      format: combine(
        colorize({ all: true }),
        timestamp({ format: 'YYYY-MM-DD HH:mm:ss' })
      )
    }),
    new DailyRotateFile({
      filename: path.join(logDir, 'application-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      zippedArchive: true,
      maxFiles: 30
    })
  ]
})

module.exports = logger
