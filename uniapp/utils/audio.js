import { getBaseUrl } from '@/api/client.js'

let innerAudio = null
let playingId = null
let onPlayingChange = null

/** 手机端把 127.0.0.1 换成设置页里的 Mac 局域网地址 */
export function resolveAudioUrl(url) {
  if (!url) return ''
  const base = getBaseUrl().replace(/\/$/, '')
  let u = String(url).trim()
  if (u.startsWith('/')) {
    return base + u
  }
  if (/^https?:\/\/127\.0\.0\.1/i.test(u)) {
    return u.replace(/^https?:\/\/127\.0\.0\.1(?::\d+)?/i, base)
  }
  if (/^https?:\/\/localhost/i.test(u)) {
    return u.replace(/^https?:\/\/localhost(?::\d+)?/i, base)
  }
  return u
}

export function setPlayingCallback(cb) {
  onPlayingChange = cb
}

export function getRecorder() {
  return uni.getRecorderManager()
}

export function createPlayer() {
  if (innerAudio) {
    innerAudio.destroy()
  }
  innerAudio = uni.createInnerAudioContext()
  try {
    innerAudio.obeyMuteSwitch = false
  } catch (_) {
    /* 部分 App 基座 obeyMuteSwitch 为只读，忽略即可 */
  }
  return innerAudio
}

export function estimateDuration(text) {
  if (!text) return 1
  return Math.max(1, Math.min(60, Math.ceil(text.length / 4)))
}

export function voiceBarWidth(durationSec) {
  const sec = Math.max(1, Math.min(60, durationSec || 1))
  return 120 + sec * 12
}

export function playUrl(url, msgId, onEnd, onError) {
  const src = resolveAudioUrl(url)
  if (!src) {
    onError && onError(new Error('无效音频地址'))
    return null
  }
  stopPlayer()
  const player = createPlayer()
  playingId = msgId
  onPlayingChange && onPlayingChange(msgId)

  let started = false
  const doPlay = () => {
    if (started) return
    started = true
    try {
      player.play()
    } catch (e) {
      started = false
      playingId = null
      onPlayingChange && onPlayingChange(null)
      onError && onError(e)
    }
  }

  player.onEnded(() => {
    playingId = null
    onPlayingChange && onPlayingChange(null)
    onEnd && onEnd()
  })
  player.onError((e) => {
    playingId = null
    onPlayingChange && onPlayingChange(null)
    onError && onError(new Error(e?.errMsg || '音频播放失败'))
  })
  player.onCanplay(() => doPlay())
  player.src = src
  setTimeout(doPlay, 300)
  return player
}

export function stopPlayer() {
  if (innerAudio) {
    innerAudio.stop()
    innerAudio.destroy()
    innerAudio = null
  }
  playingId = null
  onPlayingChange && onPlayingChange(null)
}

export function getPlayingId() {
  return playingId
}

export {
  loadMessages,
  saveMessages,
  clearMessages,
  migrateLegacyMessages
} from '@/utils/chat-store.js'
