// alias.config.js
const path = require('path')
const moduleAlias = require('module-alias')

// NODE_ENV 또는 실행 파일 위치 기준으로 환경 판단
const isProduction =
  process.env.NODE_ENV === 'production' || __dirname.includes('dist')

// 기준 디렉토리 설정 (상대경로가 아니라 절대경로로 지정)
const baseDir = path.resolve(__dirname, isProduction ? '../dist' : '../src')

// 실제 alias 등록
moduleAlias.addAliases({
  '@': path.join(baseDir),
  '@api': path.join(baseDir, 'api'),
  '@db': path.join(baseDir, 'db'),
  '@player': path.join(baseDir, 'player'),
  '@logger': path.join(baseDir, 'logger'),
  '@web': path.join(baseDir, 'web')
  // 필요한 alias 계속 추가
})
