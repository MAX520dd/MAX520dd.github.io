import { autoConfigureServer } from '@/utils/server-auto.js'

const STORAGE_KEY = 'server_base'
/** 模拟器 / HBuilder 浏览器调试；真机请在设置页填写 Mac 局域网地址 */
/** 浏览器 / 模拟器调试默认后端（与 config/server.local.js 保持一致） */
const DEFAULT_BASE_DEV = 'http://192.168.43.102:8010'
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
  const base = autoConfigureServer()
  if (base) return base
  if (isNativeMobileApp()) {
    return autoConfigureServer(true)
  }
  return normalizeBaseUrl(DEFAULT_BASE_DEV)
}

export function getBaseUrl() {
  const base = autoConfigureServer()
  if (base) return base
  return isNativeMobileApp() ? autoConfigureServer(true) : normalizeBaseUrl(DEFAULT_BASE_DEV)
}

export function setBaseUrl(url) {
  const normalized = normalizeBaseUrl(url)
  if (!normalized) {
    throw new Error('请填写服务端地址')
  }
  if (isNativeMobileApp() && isLocalhostUrl(normalized)) {
    throw new Error('真机请使用 Mac 局域网 IP，不要使用 127.0.0.1 或 localhost')
  }
  uni.setStorageSync(STORAGE_KEY, normalized)
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
  const base = assertServerConfigured()
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${base}${options.url}`,
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
      `连上的不是本项目的语音后端（端口可能被 HBuilder 占用）。请用 ${DEFAULT_PORT_HINT} 启动后端，默认地址 ${DEFAULT_BASE_DEV}`
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
  const base = assertServerConfigured()
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${base}/v1/voice/chat`,
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
