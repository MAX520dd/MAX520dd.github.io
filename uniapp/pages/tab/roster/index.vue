<template>
  <view class="page">
    <view class="section-head">
      <text class="section-title">罗德岛干员</text>
      <text class="section-sub">选择后即可在「通信」中对话</text>
    </view>

    <view v-if="loading" class="loading">
      <text>加载干员档案…</text>
    </view>

    <scroll-view v-else scroll-y class="list">
      <view
        v-for="p in personas"
        :key="p.id"
        class="row"
        hover-class="row-hover"
        @click="selectPersona(p)"
      >
        <image class="avatar" :src="avatarFor(p.id)" mode="aspectFill" />
        <view class="body">
          <view class="name-row">
            <text class="name">{{ p.name }}</text>
            <text v-if="activeId === p.id" class="badge">对接中</text>
          </view>
          <text class="desc">{{ p.description || '暂无简介' }}</text>
          <text v-if="p.modes && p.modes.length" class="modes">
            模式：{{ modeSummary(p) }}
          </text>
        </view>
        <text class="arrow">›</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { fetchPersonas } from '@/api/client.js'
import { ensureSession, personaAvatar } from '@/utils/chat-store.js'

export default {
  data() {
    return {
      personas: [],
      activeId: '',
      loading: true
    }
  },
  onShow() {
    this.activeId = uni.getStorageSync('persona_id') || ''
    this.loadPersonas()
  },
  methods: {
    async loadPersonas() {
      this.loading = true
      try {
        this.personas = await fetchPersonas()
      } catch {
        this.personas = [
          {
            id: 'skadi',
            name: '斯卡蒂',
            avatar: '/static/avatar-skadi.png',
            description: '主线深海猎人：沉默寡言、外冷内热',
            modes: ['cold', 'vulnerable'],
            mode_labels: { cold: '冷淡戒备', vulnerable: '脆弱真心' }
          },
          {
            id: 'skadi_corrupting',
            name: '浊心斯卡蒂',
            avatar: '/static/avatar-skadi-corrupting.png',
            description: 'if线红蒂：病态温柔、偏执占有',
            modes: ['gentle', 'plead'],
            mode_labels: { gentle: '温柔占有', plead: '清醒哀求' }
          }
        ]
      } finally {
        this.loading = false
      }
    },
    avatarFor(id) {
      const p = this.personas.find((x) => x.id === id)
      return p?.avatar || personaAvatar(id)
    },
    modeSummary(p) {
      const labels = p.mode_labels || {}
      return (p.modes || []).map((m) => labels[m] || m).join(' / ')
    },
    selectPersona(p) {
      uni.setStorageSync('persona_id', p.id)
      uni.setStorageSync('persona_mode', 'auto')
      this.activeId = p.id
      ensureSession(p.id, p.name)
      uni.showActionSheet({
        itemList: ['开始对话', '仅设为当前干员'],
        success: (res) => {
          if (res.tapIndex === 0) {
            uni.navigateTo({
              url: `/pages/chat/index?persona_id=${encodeURIComponent(p.id)}`
            })
          } else {
            uni.showToast({ title: `已对接 ${p.name}`, icon: 'success' })
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #ededed;
}
.section-head {
  padding: 24rpx 32rpx 8rpx;
  background: #fff;
  border-bottom: 1rpx solid #e6e6e6;
}
.section-title {
  display: block;
  font-size: 26rpx;
  color: #888;
}
.section-sub {
  display: block;
  font-size: 24rpx;
  color: #b2b2b2;
  margin-top: 4rpx;
}
.loading {
  padding: 80rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}
.list {
  height: calc(100vh - 120rpx);
}
.row {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 28rpx 32rpx;
  background: #fff;
  border-bottom: 1rpx solid #ededed;
}
.row-hover {
  background: #f5f5f5;
}
.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 8rpx;
  flex-shrink: 0;
  background: #ddd;
}
.body {
  flex: 1;
  margin-left: 24rpx;
  overflow: hidden;
}
.name-row {
  display: flex;
  flex-direction: row;
  align-items: center;
}
.name {
  font-size: 34rpx;
  color: #000;
  font-weight: 500;
}
.badge {
  margin-left: 12rpx;
  font-size: 22rpx;
  color: #07c160;
  border: 1rpx solid #07c160;
  border-radius: 6rpx;
  padding: 2rpx 10rpx;
}
.desc {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #666;
  line-height: 1.4;
}
.modes {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #999;
}
.arrow {
  font-size: 40rpx;
  color: #c8c8c8;
  margin-left: 8rpx;
}
</style>
