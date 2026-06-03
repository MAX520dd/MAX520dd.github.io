<template>
  <view class="page">
    <view class="header-card">
      <view class="avatar-wrap" @click="pickAvatar">
        <image class="avatar" :src="avatarSrc" mode="aspectFill" />
        <text class="avatar-tip">点击更换头像</text>
      </view>
      <view class="header-info">
        <text class="codename">{{ profile.codename }}</text>
        <text class="affiliation">{{ profile.affiliation }}</text>
        <text class="orundum">合成玉 {{ wallet.orundum }}</text>
      </view>
    </view>

    <view class="status-card">
      <text class="card-title">博士状态（仅影响推理语气，不会变成特殊对白）</text>
      <view
        v-for="dim in dimensions"
        :key="dim.key"
        class="status-row tap-row"
        hover-class="row-hover"
        @click="pickDimension(dim)"
      >
        <text class="label">{{ dim.label }}</text>
        <text class="value" :class="valueClass(dim.key)">{{ profile[dim.key] }}</text>
        <text class="chevron">›</text>
      </view>
    </view>

    <view class="status-card compact">
      <view class="status-row">
        <text class="label">当前对接</text>
        <text class="value highlight">{{ activePersonaName || '未选择' }}</text>
      </view>
      <view v-if="activeModeLabel" class="status-row">
        <text class="label">对话模式</text>
        <text class="value">{{ activeModeLabel }}</text>
      </view>
    </view>

    <view class="menu-group">
      <view class="menu-item" hover-class="menu-hover" @click="goSpecialItems">
        <text class="menu-label">特殊物品</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" hover-class="menu-hover" @click="resetDoctorState">
        <text class="menu-label">恢复默认状态</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" hover-class="menu-hover" @click="goSettings">
        <text class="menu-label">服务端与音色设置</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" hover-class="menu-hover" @click="goRoster">
        <text class="menu-label">干员名单</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" hover-class="menu-hover" @click="showAbout">
        <text class="menu-label">关于</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <view class="tip-block">
      <text class="tip-title">使用提示</text>
      <text class="tip-line">仅在与默认值不同时，才会在后台推理里纳入情境</text>
      <text class="tip-line">不同干员内心把握不同，但对白不会宣读状态栏</text>
    </view>
  </view>
</template>

<script>
import { fetchPersonas, fetchDoctorStates } from '@/api/client.js'
import {
  loadPlayerProfile,
  savePlayerProfile,
  getPlayerAvatar,
  chooseAndSavePlayerAvatar
} from '@/utils/chat-store.js'
import { getWallet } from '@/utils/game-store.js'
import {
  DOCTOR_DIMENSIONS,
  DOCTOR_STATE_DEFAULTS,
  applyDoctorStateMeta,
  applyDoctorStateDefaults
} from '@/utils/doctor-state.js'

export default {
  data() {
    return {
      profile: loadPlayerProfile(),
      wallet: getWallet(),
      avatarSrc: getPlayerAvatar(),
      dimensions: DOCTOR_DIMENSIONS,
      activePersonaName: '',
      activeModeLabel: '',
      personaMap: {}
    }
  },
  onShow() {
    this.profile = loadPlayerProfile()
    this.wallet = getWallet()
    this.avatarSrc = getPlayerAvatar()
    this.loadDoctorMeta()
    this.loadActivePersona()
  },
  methods: {
    async loadDoctorMeta() {
      try {
        const meta = await fetchDoctorStates()
        this.dimensions = applyDoctorStateMeta(meta)
        const defaults = applyDoctorStateDefaults(meta)
        const p = loadPlayerProfile()
        let changed = false
        this.dimensions.forEach((d) => {
          if (!p[d.key] && defaults[d.key]) {
            p[d.key] = defaults[d.key]
            changed = true
          }
        })
        if (changed) savePlayerProfile(p)
        this.profile = loadPlayerProfile()
      } catch {
        this.dimensions = DOCTOR_DIMENSIONS
      }
    },
    valueClass(key) {
      const v = this.profile[key] || ''
      if (key === 'mentalState' || key === 'sanity') {
        if (v.includes('不稳') || v.includes('危险') || v.includes('濒临')) return 'warn'
      }
      if (key === 'injury' && (v === '重伤' || v === '病危')) return 'warn'
      return ''
    },
    pickDimension(dim) {
      uni.showActionSheet({
        itemList: dim.values,
        success: (res) => {
          const profile = loadPlayerProfile()
          profile[dim.key] = dim.values[res.tapIndex]
          savePlayerProfile(profile)
          this.profile = loadPlayerProfile()
          uni.showToast({ title: '已更新', icon: 'success' })
        }
      })
    },
    resetDoctorState() {
      uni.showModal({
        title: '恢复默认',
        content: '将所有博士状态恢复为默认值？',
        success: (res) => {
          if (!res.confirm) return
          const profile = loadPlayerProfile()
          Object.assign(profile, DOCTOR_STATE_DEFAULTS)
          savePlayerProfile(profile)
          this.profile = loadPlayerProfile()
          uni.showToast({ title: '已恢复', icon: 'success' })
        }
      })
    },
    async loadActivePersona() {
      const personaId = uni.getStorageSync('persona_id') || ''
      const mode = uni.getStorageSync('persona_mode') || 'auto'
      try {
        const list = await fetchPersonas()
        list.forEach((p) => {
          this.personaMap[p.id] = p
        })
      } catch {
        this.personaMap = {
          skadi: { name: '斯卡蒂', mode_labels: { cold: '冷淡戒备', vulnerable: '脆弱真心' } },
          skadi_corrupting: {
            name: '浊心斯卡蒂',
            mode_labels: { gentle: '温柔占有', plead: '清醒哀求' }
          }
        }
      }
      const p = this.personaMap[personaId]
      this.activePersonaName = p?.name || ''
      if (mode === 'auto') {
        this.activeModeLabel = '自动'
      } else {
        this.activeModeLabel = (p?.mode_labels || {})[mode] || mode
      }
    },
    async pickAvatar() {
      try {
        const path = await chooseAndSavePlayerAvatar()
        this.avatarSrc = path
        uni.showToast({ title: '头像已更新', icon: 'success' })
      } catch (e) {
        const msg = e.message || ''
        if (!msg.includes('cancel') && !msg.includes('取消')) {
          uni.showToast({ title: msg.slice(0, 30), icon: 'none' })
        }
      }
    },
    goSpecialItems() {
      uni.navigateTo({ url: '/pages/tab/profile/special-items' })
    },
    goSettings() {
      uni.navigateTo({ url: '/pages/settings/index' })
    },
    goRoster() {
      uni.switchTab({ url: '/pages/tab/roster/index' })
    },
    showAbout() {
      uni.showModal({
        title: '浊心斯卡蒂 · 语音对话',
        content: '罗德岛干员语音通信演示。后端需在本机启动并配置 API 密钥。',
        showCancel: false
      })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #ededed;
  padding-bottom: 32rpx;
}
.header-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 48rpx 32rpx 40rpx;
  background: #fff;
  margin-bottom: 24rpx;
}
.avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 12rpx;
  background: #ddd;
}
.avatar-tip {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #07c160;
}
.header-info {
  flex: 1;
  margin-left: 28rpx;
}
.codename {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  color: #000;
}
.affiliation {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  color: #888;
}
.orundum {
  display: block;
  margin-top: 12rpx;
  font-size: 30rpx;
  color: #e6a23c;
  font-weight: 500;
}
.status-card {
  background: #fff;
  padding: 28rpx 32rpx;
  margin-bottom: 24rpx;
}
.status-card.compact {
  padding-top: 16rpx;
}
.card-title {
  display: block;
  font-size: 26rpx;
  color: #888;
  margin-bottom: 20rpx;
}
.status-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}
.status-row:last-child {
  border-bottom: none;
}
.tap-row {
  padding-right: 8rpx;
}
.row-hover {
  background: #f8f8f8;
}
.label {
  font-size: 30rpx;
  color: #666;
  flex-shrink: 0;
}
.value {
  flex: 1;
  text-align: right;
  font-size: 30rpx;
  color: #000;
  margin-right: 8rpx;
}
.value.highlight {
  color: #07c160;
  font-weight: 500;
}
.value.warn {
  color: #e6a23c;
}
.chevron {
  font-size: 32rpx;
  color: #c8c8c8;
}
.menu-group {
  background: #fff;
  margin-bottom: 24rpx;
}
.menu-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 28rpx 32rpx;
  border-bottom: 1rpx solid #ededed;
}
.menu-item:last-child {
  border-bottom: none;
}
.menu-hover {
  background: #f5f5f5;
}
.menu-label {
  flex: 1;
  font-size: 32rpx;
  color: #000;
}
.menu-arrow {
  font-size: 36rpx;
  color: #c8c8c8;
}
.tip-block {
  margin: 0 24rpx;
  padding: 24rpx;
  background: #fff;
  border-radius: 12rpx;
}
.tip-title {
  display: block;
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
  margin-bottom: 16rpx;
}
.tip-line {
  display: block;
  font-size: 26rpx;
  color: #888;
  line-height: 1.6;
  margin-bottom: 8rpx;
}
</style>
