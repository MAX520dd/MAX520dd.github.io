/**
 * 优先使用 server.local.js（本地、不入库），否则 server.example.js。
 * 使用静态 import，避免 UniApp/Vite 下 require 无法加载 local 配置。
 * 首次克隆请执行 ../../scripts/setup-local-config.sh 生成 server.local.js
 */
import { AUTO_SERVER_URL as EXAMPLE_URL } from './server.example.js'
import { AUTO_SERVER_URL as LOCAL_URL } from './server.local.js'

export const AUTO_SERVER_URL = LOCAL_URL || EXAMPLE_URL || ''
