<template>
  <view class="page">
    <view v-if="items.length === 0" class="empty">
      <text>暂无特殊物品</text>
      <text class="sub">哄干员开心领取红包，或在商城赠送礼物可获得</text>
    </view>
    <scroll-view v-else scroll-y class="list">
      <view
        v-for="(item, idx) in items"
        :key="idx"
        class="card"
        @click="showDetail(item)"
      >
        <text class="icon">{{ item.icon || '🎁' }}</text>
        <view class="body">
          <text class="name">{{ item.title || item.itemId }}</text>
          <text class="meta">{{ sourceLabel(item.source) }} · {{ formatTime(item.claimedAt) }}</text>
        </view>
        <text class="arrow">›</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getSpecialItems, getCachedCatalog } from '@/utils/game-store.js'

export default {
  data() {
    return {
      items: []
    }
  },
  onShow() {
    this.items = getSpecialItems()
  },
  methods: {
    sourceLabel(s) {
      if (s === 'red_packet') return '特殊红包'
      if (s === 'gift') return '赠礼事件'
      return '收藏'
    },
    formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
    },
    showDetail(item) {
      const catalog = getCachedCatalog()
      const meta = (catalog?.special_item_meta || {})[item.itemId] || {}
      const desc = meta.desc || item.title || ''
      let content = desc
      if (item.itemId === 'gift_saltwind_memory') {
        content += '\n\n（盐风城照片请在对话记录中查看）'
      }
      uni.showModal({
        title: item.title || item.itemId,
        content,
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
}
.empty {
  padding: 120rpx 48rpx;
  text-align: center;
}
.empty text {
  display: block;
  font-size: 30rpx;
  color: #666;
}
.sub {
  margin-top: 16rpx;
  font-size: 26rpx;
  color: #999;
}
.list {
  height: 100vh;
  padding: 16rpx 24rpx;
}
.card {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: #fff;
  border-radius: 12rpx;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
}
.icon {
  font-size: 48rpx;
  width: 72rpx;
  text-align: center;
}
.body {
  flex: 1;
}
.name {
  display: block;
  font-size: 32rpx;
  color: #000;
}
.meta {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #999;
}
.arrow {
  color: #ccc;
  font-size: 36rpx;
}
</style>
