<template>
  <view class="page">
    <view v-if="sessions.length === 0" class="empty">
      <text class="empty-title">暂无通信记录</text>
      <text class="empty-hint">在「干员名单」选择干员开始对话</text>
      <button class="empty-btn" size="mini" @click="goRoster">前往干员名单</button>
    </view>

    <scroll-view v-else scroll-y class="list">
      <view
        v-for="item in sessions"
        :key="item.personaId"
        class="row"
        hover-class="row-hover"
        @click="openChat(item)"
      >
        <image class="avatar" :src="avatarFor(item.personaId)" mode="aspectFill" />
        <view class="body">
          <view class="top">
            <text class="name">{{ displayName(item) }}</text>
            <text class="time">{{ formatTime(item.updatedAt) }}</text>
          </view>
          <text class="preview">{{ item.preview || '点击开始对话' }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { fetchPersonas } from '@/api/client.js'
import {
  listSessions,
  formatSessionTime,
  personaAvatar,
  ensureSession,
  migrateLegacyMessages
} from '@/utils/chat-store.js'

export default {
  data() {
    return {
      sessions: [],
      personaMap: {}
    }
  },
  onShow() {
    migrateLegacyMessages()
    this.loadList()
  },
  methods: {
    async loadList() {
      try {
        const list = await fetchPersonas()
        const map = {}
        list.forEach((p) => {
          map[p.id] = p
        })
        this.personaMap = map
      } catch {
        this.personaMap = {
          skadi: { id: 'skadi', name: '斯卡蒂', avatar: '/static/avatar-skadi.png' },
          skadi_corrupting: {
            id: 'skadi_corrupting',
            name: '浊心斯卡蒂',
            avatar: '/static/avatar-skadi-corrupting.png'
          }
        }
      }
      const sessions = listSessions()
      sessions.forEach((s) => {
        const p = this.personaMap[s.personaId]
        if (p && !s.personaName) s.personaName = p.name
      })
      this.sessions = sessions
    },
    displayName(item) {
      return item.personaName || this.personaMap[item.personaId]?.name || item.personaId
    },
    avatarFor(personaId) {
      return this.personaMap[personaId]?.avatar || personaAvatar(personaId)
    },
    formatTime(ts) {
      return formatSessionTime(ts)
    },
    openChat(item) {
      const p = this.personaMap[item.personaId]
      ensureSession(item.personaId, p?.name || item.personaName)
      uni.setStorageSync('persona_id', item.personaId)
      uni.navigateTo({
        url: `/pages/chat/index?persona_id=${encodeURIComponent(item.personaId)}`
      })
    },
    goRoster() {
      uni.switchTab({ url: '/pages/tab/roster/index' })
    }
  }
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #fff;
}
.list {
  height: 100vh;
}
.row {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 24rpx 32rpx;
  border-bottom: 1rpx solid #ededed;
}
.row-hover {
  background: #ececec;
}
.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 8rpx;
  flex-shrink: 0;
  background: #ddd;
}
.body {
  flex: 1;
  margin-left: 24rpx;
  overflow: hidden;
}
.top {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}
.name {
  font-size: 32rpx;
  color: #000;
  font-weight: 500;
}
.time {
  font-size: 24rpx;
  color: #b2b2b2;
  flex-shrink: 0;
  margin-left: 16rpx;
}
.preview {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  padding: 120rpx 48rpx;
  text-align: center;
}
.empty-title {
  display: block;
  font-size: 32rpx;
  color: #333;
  margin-bottom: 16rpx;
}
.empty-hint {
  display: block;
  font-size: 26rpx;
  color: #999;
  margin-bottom: 32rpx;
}
.empty-btn {
  background: #07c160;
  color: #fff;
}
</style>
