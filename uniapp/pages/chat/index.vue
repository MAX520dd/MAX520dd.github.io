<template>
  <view class="page">
    <scroll-view
      class="chat-scroll"
      scroll-y
      :scroll-into-view="scrollIntoView"
      scroll-with-animation
      :enable-flex="true"
    >
      <view v-if="messages.length === 0" class="empty">
        <text>点击下方输入框旁麦克风，或按住说话</text>
      </view>

      <view
        v-for="(msg, index) in messages"
        :key="msg.id"
        :id="'msg-' + index"
        class="msg-row"
        :class="msg.role"
      >
        <template v-if="msg.type === 'red_packet'">
          <image
            class="avatar"
            :src="assistantAvatar"
            mode="aspectFill"
            @tap.stop="openRelationPanel"
          />
          <view class="red-packet-wrap" @tap.stop="claimRedPacket(msg)">
            <view class="red-packet" :class="{ claimed: msg.claimed }">
              <text class="rp-icon">{{ msg.icon || '🧧' }}</text>
              <view class="rp-body">
                <text class="rp-title">{{ msg.title || '特殊红包' }}</text>
                <text class="rp-desc">{{ msg.claimed ? '已领取' : '点击领取 · +600 合成玉' }}</text>
              </view>
            </view>
          </view>
        </template>

        <template v-else>
        <image
          v-if="msg.role === 'assistant'"
          class="avatar"
          :src="assistantAvatar"
          mode="aspectFill"
          @tap.stop="openRelationPanel"
        />
        <view
          class="bubble-wrap"
          :class="{ 'bubble-playable': canPlayAudio(msg) }"
          @tap.stop="onTapBubble(msg)"
        >
          <!-- 可播放语音：button 保证 App 内 tap 可靠 -->
          <button
            v-if="msg.type === 'voice' && canPlayAudio(msg)"
            class="voice-hit"
            hover-class="voice-hit-hover"
            plain
            @tap.stop="playVoice(msg)"
          >
            <view
              class="voice-bar"
              :class="[msg.role, { playing: playingId === msg.id }]"
              :style="{ width: barWidth(msg.duration) + 'rpx' }"
            >
              <view v-if="msg.role === 'assistant'" class="voice-waves">
                <view class="wave" /><view class="wave" /><view class="wave" />
              </view>
              <text class="voice-dur">{{ msg.duration }}''</text>
              <view v-if="msg.role === 'user'" class="voice-waves">
                <view class="wave" /><view class="wave" /><view class="wave" />
              </view>
            </view>
          </button>
          <!-- 用户录音（无回放地址） -->
          <view
            v-else-if="msg.type === 'voice'"
            class="voice-bar disabled"
            :class="msg.role"
            :style="{ width: barWidth(msg.duration) + 'rpx' }"
          >
            <text class="voice-dur">{{ msg.duration }}''</text>
          </view>
          <!-- 文字气泡 -->
          <view v-if="msg.content && msg.type !== 'voice'" class="text-bubble" :class="msg.role">
            <text class="text-content">{{ msg.content }}</text>
          </view>
          <!-- 对白文稿 -->
          <view
            v-if="msg.content && msg.type === 'voice' && msg.showText"
            class="text-sub"
          >
            <text>{{ msg.content }}</text>
          </view>
          <!-- 神态 / 语气（<cot> 解析） -->
          <view
            v-if="msg.role === 'assistant' && msg.stage"
            class="stage-caption"
          >
            <text>— {{ msg.stage }}</text>
          </view>
          <image
            v-if="msg.image_url"
            class="event-image"
            :src="resolveMediaUrl(msg.image_url)"
            mode="aspectFill"
            @tap.stop="previewImage(msg.image_url)"
          />
        </view>
        <image
          v-if="msg.role === 'user'"
          class="avatar"
          :src="userAvatar"
          mode="aspectFill"
        />
        </template>
      </view>

      <view v-if="loading" class="loading-tip">
        <text>{{ loadingText }}</text>
      </view>
      <view id="msg-bottom" class="scroll-anchor" />
    </scroll-view>

    <!-- 微信式底部栏 -->
    <view class="footer safe-bottom">
      <view class="footer-bar">
        <view class="icon-btn" @click="toggleInputMode">
          <text class="iconfont">{{ voiceMode ? '⌨️' : '🎤' }}</text>
        </view>

        <view v-if="!voiceMode" class="input-wrap">
          <input
            class="text-input"
            v-model="inputText"
            placeholder="输入消息..."
            placeholder-class="ph"
            confirm-type="send"
            @confirm="sendText"
          />
        </view>
        <view
          v-else
          class="hold-btn"
          :class="{ recording: isRecording }"
          @touchstart.prevent="startRecord"
          @touchend.prevent="stopRecord"
          @touchcancel.prevent="cancelRecord"
        >
          <text>{{ isRecording ? '松开 发送' : '按住 说话' }}</text>
        </view>

        <view v-if="!voiceMode" class="send-wrap" @click="sendText">
          <text class="send-label">发送</text>
        </view>
        <view v-else class="icon-btn placeholder-btn" />
      </view>
    </view>

    <persona-relation-panel
      :visible="relationPanelVisible"
      :persona-name="personaName"
      :relation="relation"
      @close="relationPanelVisible = false"
    />
  </view>
</template>

<script>
import PersonaRelationPanel from '@/components/persona-relation-panel.vue'
import {
  chatText,
  synthesizeTts,
  uploadVoiceChat,
  fetchPersonas,
  formatNetworkError,
  getBaseUrl
} from '@/api/client.js'
import {
  getRecorder,
  playUrl,
  stopPlayer,
  estimateDuration,
  voiceBarWidth,
  setPlayingCallback,
  resolveAudioUrl
} from '@/utils/audio.js'
import {
  loadMessages,
  saveMessages,
  ensureSession,
  migrateLegacyMessages,
  getPlayerAvatar,
  personaAvatar
} from '@/utils/chat-store.js'
import { getDoctorStatePayload } from '@/utils/doctor-state.js'
import {
  getRelation,
  applyMoodFromChat,
  claimRedPacket as claimRedPacketStore,
  getClaimRewardOrundum,
  consumePendingGiftEvent
} from '@/utils/game-store.js'

export default {
  components: { PersonaRelationPanel },
  data() {
    return {
      messages: [],
      inputText: '',
      loading: false,
      loadingText: '',
      isRecording: false,
      recordCancelled: false,
      voiceMode: false,
      scrollIntoView: '',
      personaId: 'skadi',
      personaName: '浊心斯卡蒂',
      personaMode: 'auto',
      voiceType: '',
      speed: 1.0,
      recorder: null,
      playingId: null,
      routePersonaId: '',
      personaDefaultVoice: '',
      userAvatar: getPlayerAvatar(),
      relation: getRelation('skadi_corrupting'),
      relationPanelVisible: false
    }
  },
  computed: {
    assistantAvatar() {
      return personaAvatar(this.personaId)
    },
    /** 设置页手动填写的音色优先，否则用当前干员 default_voice */
    effectiveVoiceType() {
      return this.voiceType || this.personaDefaultVoice || ''
    }
  },
  onLoad(options) {
    migrateLegacyMessages()
    const id = options?.persona_id || uni.getStorageSync('persona_id') || 'skadi_corrupting'
    this.routePersonaId = id
    this.personaId = id
    uni.setStorageSync('persona_id', id)
    this.relation = getRelation(id)
    if (options?.append_gift === '1') {
      this.$nextTick(() => this.flushPendingGiftEvent())
    }
  },
  onShow() {
    if (this.routePersonaId) {
      this.personaId = this.routePersonaId
    }
    this.messages = this.normalizeMessages(loadMessages(this.personaId))
    this.userAvatar = getPlayerAvatar()
    this.personaMode = uni.getStorageSync('persona_mode') || 'auto'
    this.voiceType = uni.getStorageSync('voice_type') || ''
    this.speed = parseFloat(uni.getStorageSync('tts_speed') || '1.0')
    this.relation = getRelation(this.personaId)
    this.loadPersonaName()
    setPlayingCallback((id) => {
      this.playingId = id
    })
    this.flushPendingGiftEvent()
  },
  onUnload() {
    stopPlayer()
    if (this.recorder) this.recorder.stop()
  },
  methods: {
    normalizeMessages(list) {
      return (list || []).map((m) => ({
        id: m.id || Date.now() + Math.random(),
        role: m.role,
        type: m.type || (m.audio_url && !m.showText ? 'voice' : 'text'),
        content: m.content || '',
        stage: m.stage || '',
        audio_url: resolveAudioUrl(m.audio_url || ''),
        image_url: m.image_url || '',
        duration: m.duration || estimateDuration(m.content),
        showText: m.showText !== false,
        title: m.title || '',
        desc: m.desc || '',
        icon: m.icon || '',
        itemId: m.itemId || '',
        claimed: !!m.claimed
      }))
    },
    resolveMediaUrl(url) {
      if (!url) return ''
      if (url.startsWith('http')) return url
      const base = getBaseUrl().replace(/\/$/, '')
      return base + url
    },
    previewImage(url) {
      const u = this.resolveMediaUrl(url)
      if (u) uni.previewImage({ urls: [u] })
    },
    openRelationPanel() {
      this.relation = getRelation(this.personaId)
      this.relationPanelVisible = true
    },
    getRelationContext() {
      const rel = getRelation(this.personaId)
      return {
        joy: rel.joy,
        affection: rel.affection,
        lastRedPacketAt: rel.lastRedPacketAt || null
      }
    },
    handleChatMeta(chatRes) {
      const { relation, redPacket } = applyMoodFromChat(
        this.personaId,
        chatRes.mood_delta,
        chatRes.emotion,
        chatRes.red_packet_offer,
        chatRes.joy_after,
        chatRes.affection_after
      )
      this.relation = relation
      if (redPacket) {
        this.appendMessage({
          role: 'assistant',
          type: 'red_packet',
          title: redPacket.title,
          desc: redPacket.desc,
          icon: redPacket.icon,
          itemId: redPacket.itemId,
          claimed: false
        })
      }
    },
    claimRedPacket(msg) {
      if (msg.claimed) return
      const res = claimRedPacketStore(msg, getClaimRewardOrundum())
      if (res.ok) {
        msg.claimed = true
        saveMessages(this.personaId, this.messages)
        uni.showToast({ title: `+${getClaimRewardOrundum()} 合成玉`, icon: 'success' })
      }
    },
    flushPendingGiftEvent() {
      const ev = consumePendingGiftEvent(this.personaId)
      if (!ev) return
      this.appendGiftEventMessages(ev)
    },
    appendGiftEventMessages(ev) {
      if (ev.reply_text) {
        const aiMsg = this.appendMessage({
          role: 'assistant',
          type: ev.audio_url ? 'voice' : 'text',
          content: ev.reply_text,
          stage: ev.stage_direction || '',
          audio_url: ev.audio_url || '',
          image_url: ev.image_url || '',
          duration: ev.duration_sec || estimateDuration(ev.reply_text),
          showText: true
        })
        if (ev.audio_url) this.playVoice(aiMsg)
      }
      if (ev.audio_url_snore) {
        setTimeout(() => {
          const snoreMsg = this.appendMessage({
            role: 'assistant',
            type: 'voice',
            content: '……',
            stage: '睡梦中轻轻呼气',
            audio_url: ev.audio_url_snore,
            duration: 3,
            showText: false
          })
          this.playVoice(snoreMsg)
        }, (ev.duration_sec || 2) * 1000 + 500)
      }
    },
    barWidth(sec) {
      return voiceBarWidth(sec)
    },
    canPlayAudio(msg) {
      return msg.type === 'voice' && !!msg.audio_url
    },
    onTapBubble(msg) {
      if (this.canPlayAudio(msg)) {
        this.playVoice(msg)
      }
    },
    toggleInputMode() {
      this.voiceMode = !this.voiceMode
    },
    async loadPersonaName() {
      try {
        const list = await fetchPersonas()
        const p = list.find((x) => x.id === this.personaId)
        if (p) {
          this.personaName = p.name
          this.personaDefaultVoice = p.default_voice || ''
          ensureSession(this.personaId, p.name)
          uni.setNavigationBarTitle({ title: p.name })
        }
      } catch {
        ensureSession(this.personaId, this.personaName)
        uni.setNavigationBarTitle({ title: this.personaName })
      }
    },
    historyForApi() {
      return this.messages
        .filter((m) => m.content)
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))
    },
    appendMessage(opts) {
      const msg = {
        id: Date.now() + Math.random(),
        role: opts.role,
        type: opts.type || 'text',
        content: opts.content || '',
        stage: opts.stage || '',
        audio_url: resolveAudioUrl(opts.audio_url || ''),
        duration: opts.duration || estimateDuration(opts.content),
        showText: opts.showText !== false
      }
      this.messages.push(msg)
      saveMessages(this.personaId, this.messages)
      this.$nextTick(() => {
        this.scrollIntoView = 'msg-bottom'
      })
      return msg
    },
    playVoice(msg) {
      if (this.loading) return
      if (!msg.audio_url) {
        uni.showToast({ title: '暂无语音', icon: 'none' })
        return
      }
      const url = resolveAudioUrl(msg.audio_url)
      playUrl(
        url,
        msg.id,
        null,
        (e) => {
          const tip = (e && e.message) || '播放失败'
          uni.showToast({
            title: tip.includes('127.0.0.1')
              ? '请在设置填写 Mac 局域网 IP'
              : tip.slice(0, 40),
            icon: 'none',
            duration: 2500
          })
        }
      )
    },
    formatError(e) {
      const raw = e.message || String(e)
      if (raw.includes('401') || raw.includes('鉴权') || raw.includes('grant')) {
        return '语音鉴权失败：请在 Mac 的 backend/.env 填写 DOUBAO_API_KEY（火山语音控制台 → API Key 管理），保存后重启后端'
      }
      if (raw.includes('mismatched') || raw.includes('Resource-Id')) {
        return '音色版本不匹配：.env 中 DOUBAO_CLONE_RESOURCE_ID 改为 seed-icl-1.0 或 seed-icl-2.0'
      }
      return formatNetworkError(e)
    },
    async sendText() {
      const text = (this.inputText || '').trim()
      if (!text || this.loading) return
      this.inputText = ''
      this.appendMessage({ role: 'user', type: 'text', content: text })
      await this.runTextPipeline(text)
    },
    async runTextPipeline(userText) {
      this.loading = true
      this.loadingText = '对方正在输入...'
      try {
        const chatRes = await chatText(
          userText,
          this.personaId,
          this.historyForApi(),
          this.personaMode,
          getDoctorStatePayload(),
          this.getRelationContext()
        )
        this.handleChatMeta(chatRes)
        this.loadingText = '合成语音...'
        const ttsRes = await synthesizeTts(
          chatRes.tts_text || chatRes.reply_text,
          this.effectiveVoiceType || chatRes.default_voice,
          this.speed,
          chatRes.emotion,
          chatRes.tts_context || chatRes.stage_direction
        )
        const dur = ttsRes.duration_sec || estimateDuration(chatRes.reply_text)
        const aiMsg = this.appendMessage({
          role: 'assistant',
          type: 'voice',
          content: chatRes.reply_text,
          stage: chatRes.stage_direction || '',
          audio_url: ttsRes.audio_url,
          duration: dur,
          showText: true
        })
        this.playVoice(aiMsg)
      } catch (e) {
        uni.showToast({ title: this.formatError(e), icon: 'none', duration: 3500 })
      } finally {
        this.loading = false
        this.loadingText = ''
      }
    },
    startRecord() {
      if (this.loading) return
      this.recordCancelled = false
      this.isRecording = true
      this.recorder = getRecorder()
      this.recorder.onStop((res) => {
        this.isRecording = false
        if (this.recordCancelled || !res.tempFilePath) return
        const dur = Math.max(1, Math.round((res.duration || 1000) / 1000))
        this.pendingVoice = { filePath: res.tempFilePath, duration: dur }
        this.handleVoiceUpload(res.tempFilePath, dur)
      })
      this.recorder.onError(() => {
        this.isRecording = false
        uni.showToast({ title: '录音失败', icon: 'none' })
      })
      this.recorder.start({ format: 'mp3', sampleRate: 16000, numberOfChannels: 1, duration: 60000 })
    },
    stopRecord() {
      if (!this.isRecording || !this.recorder) return
      this.recorder.stop()
    },
    cancelRecord() {
      this.recordCancelled = true
      this.isRecording = false
      if (this.recorder) this.recorder.stop()
    },
    async handleVoiceUpload(filePath, recordDur) {
      this.appendMessage({
        role: 'user',
        type: 'voice',
        content: '',
        duration: recordDur,
        showText: false
      })
      this.loading = true
      this.loadingText = '识别与回复中...'
      try {
        const history = JSON.stringify(this.historyForApi())
        const form = {
          persona_id: this.personaId,
          voice_type: this.effectiveVoiceType || '',
          speed: String(this.speed),
          history
        }
        if (this.personaMode && this.personaMode !== 'auto') form.mode = this.personaMode
        form.doctor_state = JSON.stringify(getDoctorStatePayload())
        const rel = this.getRelationContext()
        form.joy = String(rel.joy)
        form.affection = String(rel.affection)
        if (rel.lastRedPacketAt) form.last_red_packet_at = String(rel.lastRedPacketAt)
        const res = await uploadVoiceChat(filePath, form)
        this.handleChatMeta(res)
        if (res.user_text) {
          const userIdx = this.messages.length - 1
          const um = this.messages[userIdx]
          if (um && um.role === 'user') {
            um.content = res.user_text
            um.showText = true
            saveMessages(this.personaId, this.messages)
          }
        }
        const dur = res.duration_sec || estimateDuration(res.reply_text)
        const aiMsg = this.appendMessage({
          role: 'assistant',
          type: 'voice',
          content: res.reply_text,
          stage: res.stage_direction || '',
          audio_url: res.audio_url,
          duration: dur,
          showText: true
        })
        if (res.audio_url) this.playVoice(aiMsg)
      } catch (e) {
        uni.showToast({ title: this.formatError(e), icon: 'none', duration: 3500 })
      } finally {
        this.loading = false
        this.loadingText = ''
      }
    }
  }
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #ededed;
}
.chat-scroll {
  flex: 1;
  padding: 16rpx 0;
  box-sizing: border-box;
}
.scroll-anchor {
  height: 24rpx;
}
.empty {
  text-align: center;
  color: #999;
  font-size: 28rpx;
  margin-top: 200rpx;
  padding: 0 48rpx;
}
.msg-row {
  display: flex;
  align-items: flex-start;
  padding: 20rpx 24rpx;
  gap: 16rpx;
}
.msg-row.user {
  flex-direction: row;
  justify-content: flex-end;
}
.msg-row.assistant {
  flex-direction: row;
  justify-content: flex-start;
}
.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 8rpx;
  flex-shrink: 0;
  background: #ddd;
}
.bubble-wrap {
  max-width: 72%;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.msg-row.user .bubble-wrap {
  align-items: flex-end;
}
.msg-row.assistant .bubble-wrap {
  align-items: flex-start;
}
.text-bubble {
  padding: 18rpx 24rpx;
  border-radius: 8rpx;
  font-size: 32rpx;
  line-height: 1.45;
  word-break: break-all;
}
.text-bubble.user {
  background: #95ec69;
  color: #000;
}
.text-bubble.assistant {
  background: #fff;
  color: #000;
}
.text-sub {
  font-size: 28rpx;
  color: #333;
  padding: 8rpx 12rpx;
  max-width: 100%;
  background: rgba(255, 255, 255, 0.65);
  border-radius: 6rpx;
}
.stage-caption {
  font-size: 22rpx;
  color: #7a6a8a;
  padding: 4rpx 12rpx 0;
  max-width: 100%;
  line-height: 1.4;
  font-style: italic;
}
.voice-hit {
  padding: 0;
  margin: 0;
  border: none;
  background: transparent;
  line-height: 1;
  display: block;
}
.voice-hit::after {
  border: none;
}
.voice-hit-hover {
  opacity: 0.85;
}
.bubble-playable {
  position: relative;
  z-index: 1;
}
.voice-bar {
  display: flex;
  align-items: center;
  padding: 18rpx 24rpx;
  border-radius: 8rpx;
  min-width: 160rpx;
  max-width: 480rpx;
  gap: 16rpx;
}
.voice-bar.disabled {
  opacity: 0.75;
}
.voice-bar.user {
  background: #95ec69;
  flex-direction: row-reverse;
}
.voice-bar.assistant {
  background: #fff;
}
.voice-bar.playing .wave {
  animation: wave 0.6s ease-in-out infinite alternate;
}
.voice-dur {
  font-size: 28rpx;
  color: #333;
  flex-shrink: 0;
}
.voice-waves {
  display: flex;
  align-items: center;
  gap: 4rpx;
  height: 32rpx;
}
.wave {
  width: 6rpx;
  height: 16rpx;
  background: #333;
  border-radius: 2rpx;
}
.voice-bar.user .wave {
  background: #2d6b1f;
}
.wave:nth-child(2) {
  height: 24rpx;
}
.wave:nth-child(3) {
  height: 18rpx;
}
@keyframes wave {
  from {
    transform: scaleY(0.6);
  }
  to {
    transform: scaleY(1.2);
  }
}
.loading-tip {
  text-align: center;
  font-size: 24rpx;
  color: #999;
  padding: 12rpx;
}
.footer {
  background: #f7f7f7;
  border-top: 1rpx solid #dcdcdc;
}
.footer-bar {
  display: flex;
  align-items: center;
  padding: 16rpx 20rpx;
  gap: 16rpx;
}
.icon-btn {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  flex-shrink: 0;
}
.placeholder-btn {
  opacity: 0;
}
.input-wrap {
  flex: 1;
  background: #fff;
  border-radius: 8rpx;
  border: 1rpx solid #e0e0e0;
  padding: 0 20rpx;
}
.text-input {
  height: 72rpx;
  font-size: 30rpx;
  color: #000;
}
.ph {
  color: #bbb;
}
.hold-btn {
  flex: 1;
  height: 72rpx;
  line-height: 72rpx;
  text-align: center;
  background: #fff;
  border-radius: 8rpx;
  border: 1rpx solid #e0e0e0;
  font-size: 30rpx;
  color: #333;
}
.hold-btn.recording {
  background: #cfcfcf;
}
.send-wrap {
  padding: 0 8rpx;
}
.send-label {
  font-size: 30rpx;
  color: #576b95;
}
.safe-bottom {
  padding-bottom: env(safe-area-inset-bottom);
}
.red-packet-wrap {
  max-width: 72%;
}
.red-packet {
  display: flex;
  flex-direction: row;
  align-items: center;
  background: linear-gradient(135deg, #e85d4c 0%, #c93a2e 100%);
  border-radius: 12rpx;
  padding: 24rpx 28rpx;
  min-width: 360rpx;
}
.red-packet.claimed {
  opacity: 0.55;
}
.rp-icon {
  font-size: 56rpx;
  margin-right: 20rpx;
}
.rp-title {
  display: block;
  font-size: 30rpx;
  color: #fff;
  font-weight: 600;
}
.rp-desc {
  display: block;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.85);
  margin-top: 6rpx;
}
.event-image {
  width: 400rpx;
  height: 260rpx;
  border-radius: 8rpx;
  margin-top: 8rpx;
}
</style>
