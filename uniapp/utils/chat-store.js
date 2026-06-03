const LEGACY_KEY = 'chat_messages'
const MESSAGES_PREFIX = 'chat_messages_'
const SESSIONS_KEY = 'chat_sessions'
const PLAYER_KEY = 'player_profile'

const DEFAULT_AVATAR = '/static/avatar-user.png'

import { DOCTOR_STATE_DEFAULTS } from '@/utils/doctor-state.js'

const DEFAULT_PLAYER = {
  codename: '博士',
  affiliation: '罗德岛',
  note: '',
  avatarPath: '',
  ...DOCTOR_STATE_DEFAULTS
}

export function getPlayerAvatar() {
  const p = loadPlayerProfile()
  return p.avatarPath || DEFAULT_AVATAR
}

/** 从相册选择并保存博士头像到本地持久路径 */
export function chooseAndSavePlayerAvatar() {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const temp = res.tempFilePaths?.[0]
        if (!temp) {
          reject(new Error('未选择图片'))
          return
        }
        uni.saveFile({
          tempFilePath: temp,
          success: (saveRes) => {
            const profile = loadPlayerProfile()
            profile.avatarPath = saveRes.savedFilePath
            savePlayerProfile(profile)
            resolve(saveRes.savedFilePath)
          },
          fail: (e) => reject(new Error(e.errMsg || '保存头像失败'))
        })
      },
      fail: (e) => reject(new Error(e.errMsg || '取消选择'))
    })
  })
}

function messagesKey(personaId) {
  return `${MESSAGES_PREFIX}${personaId || 'default'}`
}

function readSessions() {
  try {
    const raw = uni.getStorageSync(SESSIONS_KEY)
    return Array.isArray(raw) ? raw : []
  } catch {
    return []
  }
}

function writeSessions(list) {
  uni.setStorageSync(SESSIONS_KEY, list.slice(0, 50))
}

/** 旧版单文件聊天记录迁移到当前干员 */
export function migrateLegacyMessages() {
  try {
    const legacy = uni.getStorageSync(LEGACY_KEY)
    if (!legacy || !legacy.length) return
    const personaId = uni.getStorageSync('persona_id') || 'skadi_corrupting'
    const key = messagesKey(personaId)
    if (!uni.getStorageSync(key)?.length) {
      uni.setStorageSync(key, legacy)
      touchSession(personaId, legacy[legacy.length - 1])
    }
    uni.removeStorageSync(LEGACY_KEY)
  } catch {
    /* ignore */
  }
}

export function loadMessages(personaId) {
  migrateLegacyMessages()
  try {
    return uni.getStorageSync(messagesKey(personaId)) || []
  } catch {
    return []
  }
}

export function saveMessages(personaId, messages) {
  const list = (messages || []).slice(-100)
  uni.setStorageSync(messagesKey(personaId), list)
  if (list.length) {
    touchSession(personaId, list[list.length - 1])
  }
}

export function clearMessages(personaId) {
  if (personaId) {
    uni.removeStorageSync(messagesKey(personaId))
    writeSessions(readSessions().filter((s) => s.personaId !== personaId))
    return
  }
  readSessions().forEach((s) => {
    uni.removeStorageSync(messagesKey(s.personaId))
  })
  uni.removeStorageSync(SESSIONS_KEY)
  uni.removeStorageSync(LEGACY_KEY)
}

export function touchSession(personaId, lastMsg, personaName) {
  if (!personaId) return
  const preview = previewFromMessage(lastMsg)
  const now = Date.now()
  let sessions = readSessions()
  const idx = sessions.findIndex((s) => s.personaId === personaId)
  const row = {
    personaId,
    personaName: personaName || sessions[idx]?.personaName || '',
    preview,
    updatedAt: now
  }
  if (idx >= 0) {
    sessions[idx] = { ...sessions[idx], ...row }
  } else {
    sessions.unshift(row)
  }
  sessions.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
  writeSessions(sessions)
}

export function ensureSession(personaId, personaName) {
  const sessions = readSessions()
  if (!sessions.some((s) => s.personaId === personaId)) {
    touchSession(personaId, null, personaName)
  } else if (personaName) {
    const s = sessions.find((x) => x.personaId === personaId)
    if (s && !s.personaName) {
      touchSession(personaId, null, personaName)
    }
  }
}

export function listSessions() {
  migrateLegacyMessages()
  return readSessions().sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
}

function previewFromMessage(msg) {
  if (!msg) return ''
  const text = String(msg.content || '').trim()
  if (text) return text.length > 40 ? text.slice(0, 40) + '…' : text
  if (msg.type === 'voice') {
    return msg.role === 'user' ? '[语音]' : '[语音消息]'
  }
  return ''
}

export function formatSessionTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const sameDay =
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  if (sameDay) {
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
  return `${d.getMonth() + 1}/${d.getDate()}`
}

export function loadPlayerProfile() {
  try {
    const raw = uni.getStorageSync(PLAYER_KEY)
    return { ...DEFAULT_PLAYER, ...(raw || {}) }
  } catch {
    return { ...DEFAULT_PLAYER }
  }
}

export function savePlayerProfile(profile) {
  uni.setStorageSync(PLAYER_KEY, { ...DEFAULT_PLAYER, ...(profile || {}) })
}

/** 各干员对话头像（与 backend/data/personas.json 的 avatar 字段一致） */
const PERSONA_AVATARS = {
  skadi: '/static/avatar-skadi.png',
  skadi_corrupting: '/static/avatar-skadi-corrupting.png'
}

export function personaAvatar(personaId) {
  return PERSONA_AVATARS[personaId] || '/static/avatar-skadi-corrupting.png'
}
