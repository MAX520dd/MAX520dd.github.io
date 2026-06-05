import { getBaseUrl, resolveBackendUrl } from '@/api/client.js'

let innerAudio = null
let playingId = null
let onPlayingChange = null

/** 统一用用户配置的后端地址解析 TTS/语音 URL */
export function resolveAudioUrl(url) {
  return resolveBackendUrl(url)
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
    const errMsg = e?.errMsg || '音频播放失败'
    onError && onError(new Error(`${errMsg} (${src})`))
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
