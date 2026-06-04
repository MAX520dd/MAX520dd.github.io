<template>
  <view class="page">
    <view class="banner">
      <text class="banner-title">罗德岛补给站</text>
      <text class="banner-sub">合成玉 {{ wallet.orundum }} · 购买后从背包赠送干员</text>
    </view>

    <view v-if="loading" class="state-box">
      <text class="state-text">正在加载商品…</text>
    </view>
    <view v-else-if="loadError" class="state-box error">
      <text class="state-text">{{ loadError }}</text>
      <button class="retry-btn" size="mini" @click="load">重试</button>
      <text class="state-hint">请确认已启动后端，并在「我」→ 设置中测试连接</text>
    </view>
    <view v-else-if="!goods.length" class="state-box">
      <text class="state-text">暂无商品</text>
      <button class="retry-btn" size="mini" @click="load">刷新</button>
    </view>

    <view class="goods-list">
      <view v-for="item in goods" :key="item.id" class="goods-card">
        <view class="goods-icon">{{ item.icon }}</view>
        <view class="goods-body">
          <text class="goods-name">{{ item.name }}</text>
          <text class="goods-desc">{{ item.desc }}</text>
          <text class="goods-target">赠送给 · {{ personaLabel(item.target_persona_id) }}</text>
          <view class="goods-foot">
            <text class="price">{{ item.price }} 合成玉</text>
            <text class="stock">背包 {{ invCount(item.id) }}</text>
          </view>
          <view class="btn-row">
            <button class="buy-btn" size="mini" @click="buy(item)">购买</button>
            <button
              class="send-btn"
              size="mini"
              :disabled="invCount(item.id) < 1"
              @click="sendGift(item)"
            >
              赠送
            </button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { fetchGameCatalog, fetchPersonas, triggerGift, formatNetworkError } from '@/api/client.js'
import { CATALOG_FALLBACK } from '@/config/catalog-fallback.js'
import {
  getWallet,
  buyShopItem,
  getInventoryCount,
  cacheCatalog,
  getCachedCatalog,
  setPendingGiftEvent,
  consumeInventoryItem,
  recordGiftSpecialItem
} from '@/utils/game-store.js'

export default {
  data() {
    return {
      goods: [],
      wallet: getWallet(),
      personas: [],
      catalog: null,
      loading: false,
      loadError: '',
      catalogOffline: false
    }
  },
  onShow() {
    this.wallet = getWallet()
    this.load()
  },
  methods: {
    personaLabel(id) {
      const p = this.personas.find((x) => x.id === id)
      return p?.name || id
    },
    invCount(itemId) {
      return getInventoryCount(itemId)
    },
    async load() {
      this.loading = true
      this.loadError = ''
      this.catalogOffline = false
      try {
        const catalog = await fetchGameCatalog()
        if (!catalog?.shop_items?.length) {
          throw new Error('后端返回的商品列表为空')
        }
        cacheCatalog(catalog)
        this.catalog = catalog
        this.goods = catalog.shop_items
      } catch (e) {
        const msg = formatNetworkError(e)
        const c = getCachedCatalog()
        if (c?.shop_items?.length) {
          this.catalog = c
          this.goods = c.shop_items
          this.loadError = `已用上次缓存（${msg}）`
          this.catalogOffline = true
        } else {
          this.catalog = { ...CATALOG_FALLBACK }
          this.goods = CATALOG_FALLBACK.shop_items
          this.loadError = msg
          this.catalogOffline = true
          uni.showToast({
            title: '商品仅展示，赠送需连后端',
            icon: 'none',
            duration: 3000
          })
        }
      } finally {
        this.loading = false
      }
      try {
        this.personas = await fetchPersonas()
      } catch {
        this.personas = [
          { id: 'skadi', name: '斯卡蒂' },
          { id: 'skadi_corrupting', name: '浊心斯卡蒂' }
        ]
      }
    },
    buy(item) {
      const res = buyShopItem(item, this.catalog)
      if (!res.ok) {
        uni.showToast({ title: res.message, icon: 'none' })
        return
      }
      this.wallet = getWallet()
      uni.showToast({ title: '已入背包', icon: 'success' })
    },
    sendGift(item) {
      if (this.invCount(item.id) < 1) {
        uni.showToast({ title: '请先购买', icon: 'none' })
        return
      }
      const target = item.target_persona_id
      uni.showModal({
        title: '赠送礼物',
        content: `将「${item.name}」送给${this.personaLabel(target)}？`,
        success: async (r) => {
          if (!r.confirm) return
          if (!target) {
            uni.showToast({ title: '礼物配置异常，请刷新商城', icon: 'none' })
            return
          }
          if (getInventoryCount(item.id) < 1) {
            uni.showToast({ title: '背包数量不足', icon: 'none' })
            return
          }
          if (this.catalogOffline) {
            uni.showToast({
              title: '请先连接后端并刷新商城',
              icon: 'none',
              duration: 2500
            })
            return
          }
          uni.showLoading({ title: '准备惊喜...' })
          try {
            const ev = await triggerGift(target, item.id)
            if (item.event_type === 'sing' && !ev?.audio_url) {
              uni.showToast({
                title: (ev?.tts_error || '歌唱合成失败，请检查后端 TTS').slice(0, 60),
                icon: 'none',
                duration: 3500
              })
            }
            if (!consumeInventoryItem(item.id)) {
              uni.showToast({ title: '背包数量不足', icon: 'none' })
              return
            }
            const meta = (this.catalog?.special_item_meta || {})[item.id]
            recordGiftSpecialItem(item.id, meta)
            setPendingGiftEvent(target, ev)
            uni.setStorageSync('persona_id', target)
            uni.navigateTo({
              url: `/pages/chat/index?persona_id=${encodeURIComponent(target)}&append_gift=1`
            })
          } catch (e) {
            uni.showToast({ title: (e.message || '赠送失败').slice(0, 60), icon: 'none' })
          } finally {
            uni.hideLoading()
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
  padding-bottom: 32rpx;
}
.banner {
  background: linear-gradient(135deg, #1a3a52 0%, #2d5a7b 100%);
  padding: 48rpx 32rpx;
  margin-bottom: 24rpx;
}
.banner-title {
  display: block;
  font-size: 40rpx;
  color: #fff;
  font-weight: 600;
}
.banner-sub {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.75);
}
.state-box {
  margin: 24rpx;
  padding: 32rpx;
  background: #fff;
  border-radius: 12rpx;
  text-align: center;
}
.state-box.error {
  background: #fff8f0;
}
.state-text {
  display: block;
  font-size: 28rpx;
  color: #333;
  line-height: 1.5;
}
.state-hint {
  display: block;
  margin-top: 16rpx;
  font-size: 24rpx;
  color: #999;
}
.retry-btn {
  margin-top: 20rpx;
  background: #07c160;
  color: #fff;
}
.goods-list {
  padding: 0 24rpx;
}
.goods-card {
  display: flex;
  flex-direction: row;
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.goods-icon {
  font-size: 56rpx;
  width: 88rpx;
  text-align: center;
}
.goods-body {
  flex: 1;
  margin-left: 16rpx;
}
.goods-name {
  display: block;
  font-size: 32rpx;
  font-weight: 500;
}
.goods-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #888;
  line-height: 1.4;
}
.goods-target {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  color: #07c160;
}
.goods-foot {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-top: 12rpx;
}
.price {
  font-size: 28rpx;
  color: #e6a23c;
}
.stock {
  font-size: 24rpx;
  color: #999;
}
.btn-row {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
  margin-top: 16rpx;
}
.buy-btn {
  background: #07c160;
  color: #fff;
}
.send-btn {
  background: #576b95;
  color: #fff;
}
.send-btn[disabled] {
  background: #ccc;
}
</style>
