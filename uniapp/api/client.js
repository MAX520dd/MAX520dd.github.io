import { AUTO_SERVER_URL } from '@/config/server.js'
import {
  autoConfigureServer,
  markServerManual,
  readStoredServerUrl
} from '@/utils/server-auto.js'
import { clearCatalogCache } from '@/utils/game-store.js'

const STORAGE_KEY = 'server_base'
const DEFAULT_PORT_HINT = '8010'

/** 补全 http://，去掉误输入的前导 / */
export function normalizeBaseUrl(url) {
  let u = String(url || '').trim()
  if (!u) {
    return ''
  }
  u = u.replace(/\/+$/, '')
  u = u.replace(/^\/+/, '')
  if (!/^https?:\/\//i.test(u)) {
    u = `http://${u}`
  }
  return u
}

export function isNativeMobileApp() {
  try {
    const p = uni.getSystemInfoSync().platform
    return p === 'android' || p === 'ios'
  } catch {
    return false
  }
}

export function isLocalhostUrl(url) {
  const u = normalizeBaseUrl(url)
  if (!u) return false
  const m = u.match(/^https?:\/\/([^/:]+)/i)
  const host = (m ? m[1] : '').toLowerCase()
  return host === '127.0.0.1' || host === 'localhost' || host === '::1'
}

/** 真机未配置或误用 localhost 时的说明 */
export function getServerConfigHint() {
  return `请填写 Mac 局域网地址，例如 http://192.168.x.x:${DEFAULT_PORT_HINT}（终端执行 ipconfig getifaddr en0 查看 IP）。真机不能使用 127.0.0.1。`
}

export function assertServerConfigured() {
  const stored = readStoredServerUrl()
  if (stored) return stored
  const filled = autoConfigureServer(false)
  if (filled) return filled
  return normalizeBaseUrl(AUTO_SERVER_URL)
}

export function getBaseUrl() {
  return assertServerConfigured()
}

/** App 包内资源，不走后端 */
export function isAppBundledStatic(url) {
  const u = String(url || '')
  return u.includes('/static/biaoqingbao/')
}

/**
 * 将后端返回的媒体地址统一为「当前用户配置的后端根地址 + 路径」。
 * 避免 PUBLIC_BASE_URL 与 App 设置不一致导致语音/图片无法加载。
 */
export function resolveBackendUrl(url) {
  if (!url) return ''
  const u = String(url).trim()
  if (isAppBundledStatic(u)) {
    const pathMatch = u.match(/\/static\/biaoqingbao\/.*$/i)
    return pathMatch ? pathMatch[0] : u
  }
  const base = getBaseUrl().replace(/\/$/, '')
  const abs = u.match(/^https?:\/\/[^/]+(\/.*)$/i)
  if (abs) {
    const path = abs[1]
    if (isAppBundledStatic(path)) return path
    return base + path
  }
  if (u.startsWith('/')) {
    return base + u
  }
  return `${base}/${u}`
}

export function buildApiUrl(path) {
  const base = getBaseUrl().replace(/\/$/, '')
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${p}`
}

export function setBaseUrl(url) {
  const normalized = normalizeBaseUrl(url)
  if (!normalized) {
    throw new Error('请填写服务端地址')
  }
  if (isNativeMobileApp() && isLocalhostUrl(normalized)) {
    throw new Error('真机请使用 Mac 局域网 IP，不要使用 127.0.0.1 或 localhost')
  }
  const prev = readStoredServerUrl()
  if (prev && prev !== normalized) {
    clearCatalogCache()
  }
  uni.setStorageSync(STORAGE_KEY, normalized)
  markServerManual()
  return normalized
}

export function formatNetworkError(err) {
  const raw =
    (typeof err === 'string' ? err : '') ||
    err?.message ||
    err?.errMsg ||
    String(err || '')
  if (raw.includes('127.0.0.1') || raw.includes('localhost')) {
    return `真机请改设置：使用 Mac 局域网 IP（如 http://192.168.x.x:${DEFAULT_PORT_HINT}），不要用 127.0.0.1`
  }
  if (raw.includes('Failed to connect') || raw.includes('statusCode:-1') || raw.includes('abort')) {
    return `无法连接后端。请确认：①已双击启动后端 ②地址为 http://Mac的IP:${DEFAULT_PORT_HINT} ③手机与 Mac 同一 WiFi`
  }
  return raw.length > 100 ? raw.slice(0, 100) + '…' : raw
}

function parseHealthBody(data) {
  if (!data || typeof data !== 'object' || data.status !== 'ok') {
    return null
  }
  return data
}

export function request(options) {
  const apiUrl = buildApiUrl(options.url || '/')
  return new Promise((resolve, reject) => {
    uni.request({
      url: apiUrl,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...(options.header || {})
      },
      timeout: options.timeout || 120000,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          let detail = res.data?.detail ?? res.data?.message
          if (Array.isArray(detail)) {
            detail = detail.map((x) => x.msg || x.message || JSON.stringify(x)).join('; ')
          }
          if (!detail && res.data) {
            detail = typeof res.data === 'string' ? res.data : JSON.stringify(res.data)
          }
          reject(new Error(detail || `HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => reject(new Error(formatNetworkError(err?.errMsg || err)))
    })
  })
}

export async function healthCheck(checkTts = false, forceTts = false) {
  const params = []
  if (checkTts) params.push('check_tts=true')
  if (forceTts) params.push('force_tts=true')
  const q = params.length ? `?${params.join('&')}` : ''
  const data = await request({ url: `/health${q}` })
  const body = parseHealthBody(data)
  if (!body) {
    throw new Error(
      `连上的不是本项目的语音后端（端口可能被 HBuilder 占用）。请用 ${DEFAULT_PORT_HINT} 启动后端，当前请求 ${getBaseUrl()}`
    )
  }
  return body
}

export async function fetchPersonas() {
  const data = await request({ url: '/v1/personas' })
  return data.personas || []
}

export async function fetchDoctorStates() {
  const data = await request({ url: '/v1/doctor-states' })
  return data
}

export async function fetchGameCatalog() {
  return request({ url: '/v1/game/catalog' })
}

export async function triggerGift(personaId, itemId) {
  return request({
    url: '/v1/gift/trigger',
    method: 'POST',
    data: { persona_id: personaId, item_id: itemId }
  })
}

export async function chatText(text, personaId, history, mode, doctorState, relationCtx) {
  const data = {
    text,
    persona_id: personaId,
    history: history || []
  }
  if (mode && mode !== 'auto') {
    data.mode = mode
  }
  if (doctorState && Object.keys(doctorState).length) {
    data.doctor_state = doctorState
  }
  if (relationCtx) {
    if (relationCtx.joy != null) data.joy = relationCtx.joy
    if (relationCtx.affection != null) data.affection = relationCtx.affection
    if (relationCtx.lastRedPacketAt) {
      data.last_red_packet_at = relationCtx.lastRedPacketAt
    }
    if (relationCtx.lastStickerAt) {
      data.last_sticker_at = relationCtx.lastStickerAt
    }
    if (relationCtx.lastCrazyThursdayAt) {
      data.last_crazy_thursday_at = relationCtx.lastCrazyThursdayAt
    }
    if (relationCtx.lastContextualGiftAt) {
      data.last_contextual_gift_at = relationCtx.lastContextualGiftAt
    }
  }
  return request({
    url: '/v1/chat',
    method: 'POST',
    data
  })
}

export async function synthesizeTts(text, voiceType, speed, emotion, contextText, hum = false) {
  return request({
    url: '/v1/tts',
    method: 'POST',
    data: {
      text,
      voice_type: voiceType || undefined,
      speed: speed ?? 1.0,
      emotion: emotion || 'calm',
      context_text: contextText || undefined,
      hum: !!hum
    }
  })
}

export function uploadVoiceChat(filePath, formData) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: buildApiUrl('/v1/voice/chat'),
      filePath,
      name: 'file',
      formData: formData || {},
      timeout: 180000,
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(data)
          } else {
            reject(new Error(data.detail || `HTTP ${res.statusCode}`))
          }
        } catch (e) {
          reject(new Error('响应解析失败'))
        }
      },
      fail: (err) => reject(new Error(formatNetworkError(err?.errMsg || err)))
    })
  })
}
