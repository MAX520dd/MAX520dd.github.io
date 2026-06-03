/**
 * 优先读取 server.local.js（本地、不入库），否则使用 server.example.js 默认值。
 */
import { AUTO_SERVER_URL as EXAMPLE_URL } from './server.example.js'

let localUrl = ''
try {
  const local = require('./server.local.js')
  localUrl = local?.AUTO_SERVER_URL || ''
} catch {
  localUrl = ''
}

export const AUTO_SERVER_URL = localUrl || EXAMPLE_URL || ''
