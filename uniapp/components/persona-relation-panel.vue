<template>
  <view v-if="visible" class="mask" @click="close">
    <view class="panel" @click.stop>
      <text class="title">{{ personaName }}</text>
      <view class="row">
        <text class="label">好感度</text>
        <view class="bar-bg">
          <view class="bar-fill affection" :style="{ width: relation.affection + '%' }" />
        </view>
        <text class="num">{{ relation.affection }}</text>
      </view>
      <view class="row">
        <text class="label">开心度</text>
        <view class="bar-bg">
          <view class="bar-fill joy" :style="{ width: relation.joy + '%' }" />
        </view>
        <text class="num">{{ relation.joy }}</text>
      </view>
      <text v-if="relation.lastMoodDelta" class="hint">
        上轮氛围 {{ relation.lastMoodDelta > 0 ? '+' : '' }}{{ relation.lastMoodDelta }}
      </text>
      <text class="sub">博士诉说饿/累/冷/不适且好感≥55、开心≥38时，角色可能按性格主动关怀赠礼。开心度≥72且氛围回暖时还可能收到特殊红包。主线斯卡蒂玩「疯狂星期四」梗可触发彩蛋。</text>
      <button class="btn" size="mini" @click="close">关闭</button>
    </view>
  </view>
</template>

<script>
export default {
  props: {
    visible: { type: Boolean, default: false },
    personaName: { type: String, default: '' },
    relation: {
      type: Object,
      default: () => ({ affection: 100, joy: 50, lastMoodDelta: 0 })
    }
  },
  methods: {
    close() {
      this.$emit('close')
    }
  }
}
</script>

<style scoped>
.mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.panel {
  width: 600rpx;
  background: #fff;
  border-radius: 16rpx;
  padding: 40rpx 32rpx;
}
.title {
  display: block;
  font-size: 34rpx;
  font-weight: 600;
  margin-bottom: 28rpx;
  text-align: center;
}
.row {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 20rpx;
}
.label {
  width: 120rpx;
  font-size: 28rpx;
  color: #666;
}
.bar-bg {
  flex: 1;
  height: 16rpx;
  background: #eee;
  border-radius: 8rpx;
  overflow: hidden;
  margin: 0 16rpx;
}
.bar-fill {
  height: 100%;
  border-radius: 8rpx;
}
.bar-fill.affection {
  background: #07c160;
}
.bar-fill.joy {
  background: #e6a23c;
}
.num {
  width: 64rpx;
  text-align: right;
  font-size: 28rpx;
}
.hint {
  display: block;
  font-size: 26rpx;
  color: #888;
  margin-bottom: 8rpx;
}
.sub {
  display: block;
  font-size: 24rpx;
  color: #aaa;
  line-height: 1.5;
  margin-bottom: 24rpx;
}
.btn {
  width: 100%;
}
</style>
