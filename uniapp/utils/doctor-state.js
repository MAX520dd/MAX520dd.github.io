/** 博士状态维度（与 backend/data/doctor_states.json 同步） */

export const DOCTOR_STATE_DEFAULTS = {
  mentalState: '稳定',
  fatigue: '正常',
  dutyStatus: '在岗',
  stress: '一般',
  sleep: '充足',
  injury: '完好',
  sanity: '稳固'
}

export const DOCTOR_DIMENSIONS = [
  { key: 'mentalState', label: '神志', values: ['稳定', '轻度波动', '中度压力', '神志不稳', '濒临失常'] },
  { key: 'fatigue', label: '疲劳', values: ['精神饱满', '正常', '轻度疲劳', '深度疲惫', '透支'] },
  { key: 'dutyStatus', label: '勤务', values: ['在岗', '出外勤', '轮休', '建议休整', '失联'] },
  { key: 'stress', label: '压力', values: ['松弛', '一般', '偏高', '濒临崩溃'] },
  { key: 'sleep', label: '睡眠', values: ['充足', '略不足', '严重不足', '彻夜未眠'] },
  { key: 'injury', label: '伤势', values: ['完好', '轻伤', '重伤', '病危'] },
  { key: 'sanity', label: '理智', values: ['稳固', '动摇', '危险', '濒临迷失'] }
]

const PLAYER_KEY = 'player_profile'

function readProfile() {
  try {
    return { ...DOCTOR_STATE_DEFAULTS, ...(uni.getStorageSync(PLAYER_KEY) || {}) }
  } catch {
    return { ...DOCTOR_STATE_DEFAULTS }
  }
}

/** 供 /v1/chat 上报的博士状态对象 */
export function getDoctorStatePayload() {
  const p = readProfile()
  const out = {}
  DOCTOR_DIMENSIONS.forEach((d) => {
    out[d.key] = p[d.key] || DOCTOR_STATE_DEFAULTS[d.key]
  })
  return out
}

export function applyDoctorStateMeta(meta) {
  if (!meta || !meta.dimensions) return DOCTOR_DIMENSIONS
  return meta.dimensions
}

export function applyDoctorStateDefaults(meta) {
  if (!meta || !meta.defaults) return { ...DOCTOR_STATE_DEFAULTS }
  return { ...DOCTOR_STATE_DEFAULTS, ...meta.defaults }
}
