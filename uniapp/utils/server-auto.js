import { AUTO_SERVER_URL } from '@/config/server.js'

const STORAGE_KEY = 'server_base'

function normalizeBaseUrl(url) {
  let u = String(url || '').trim()
  if (!u) return ''
  u = u.replace(/\/+$/, '').replace(/^\/+/, '')
  if (!/^https?:\/\//i.test(u)) u = `http://${u}`
  return u
}

function isNativeMobileApp() {
  try {
    const p = uni.getSystemInfoSync().platform
    return p === 'android' || p === 'ios'
  } catch {
    return false
  }
}

function isLocalhostUrl(url) {
  const u = normalizeBaseUrl(url)
  if (!u) return false
  const m = u.match(/^https?:\/\/([^/:]+)/i)
  const host = (m ? m[1] : '').toLowerCase()
  return host === '127.0.0.1' || host === 'localhost' || host === '::1'
}

/** 真机启动时自动写入局域网后端地址，无需弹窗手动配置 */
export function autoConfigureServer(force = false) {
  const current = normalizeBaseUrl(uni.getStorageSync(STORAGE_KEY) || '')
  const target = normalizeBaseUrl(AUTO_SERVER_URL)
  if (!target) return current

  if (!isNativeMobileApp()) {
    if (!current || force) {
      uni.setStorageSync(STORAGE_KEY, target)
      return target
    }
    return current
  }

  const need = force || !current || isLocalhostUrl(current) || current !== target
  if (need) {
    uni.setStorageSync(STORAGE_KEY, target)
    return target
  }
  return current
}

export function getAutoServerUrl() {
  return normalizeBaseUrl(AUTO_SERVER_URL)
}
