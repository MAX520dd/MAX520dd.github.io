import { AUTO_SERVER_URL } from '@/config/server.js'

const STORAGE_KEY = 'server_base'
const MANUAL_KEY = 'server_manual'

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

export function isServerManual() {
  return !!uni.getStorageSync(MANUAL_KEY)
}

export function markServerManual() {
  uni.setStorageSync(MANUAL_KEY, '1')
}

export function clearServerManual() {
  uni.removeStorageSync(MANUAL_KEY)
}

/**
 * 仅在「未配置 / localhost / 用户点恢复自动地址」时写入 AUTO_SERVER_URL。
 * 用户手动保存的地址不会被编译进包的 IP 覆盖。
 */
export function autoConfigureServer(forceApplyAuto = false) {
  const current = normalizeBaseUrl(uni.getStorageSync(STORAGE_KEY) || '')
  const target = normalizeBaseUrl(AUTO_SERVER_URL)
  const manual = isServerManual()

  if (manual && !forceApplyAuto) {
    return current
  }

  if (forceApplyAuto && target) {
    uni.setStorageSync(STORAGE_KEY, target)
    clearServerManual()
    return target
  }

  const needFill =
    !current || (isNativeMobileApp() && isLocalhostUrl(current))

  if (needFill && target) {
    uni.setStorageSync(STORAGE_KEY, target)
    return target
  }

  return current
}

export function getAutoServerUrl() {
  return normalizeBaseUrl(AUTO_SERVER_URL)
}

export function readStoredServerUrl() {
  return normalizeBaseUrl(uni.getStorageSync(STORAGE_KEY) || '')
}
