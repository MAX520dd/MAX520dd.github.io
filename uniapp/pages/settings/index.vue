<template>
  <view class="page">
    <view class="section">
      <text class="label">服务端地址</text>
      <input
        class="input"
        v-model="serverBase"
        :placeholder="autoUrlHint || 'http://192.168.43.102:8010'"
        placeholder-class="placeholder"
      />
      <view v-if="serverWarn" class="warn-box">
        <text class="warn-text">真机请勿使用 127.0.0.1，请填 Mac 在 WiFi 下的 IP（端口 8010）</text>
      </view>
      <text class="hint">自动地址来自本地 uniapp/config/server.local.js（不入 Git）；换 WiFi 后请改此处并同步 backend/.env 的 PUBLIC_BASE_URL</text>
      <text v-if="autoUrlHint" class="hint">当前自动地址：{{ autoUrlHint }}</text>
      <button class="btn" size="mini" @click="resetAutoServer">恢复自动地址</button>
      <button class="btn" size="mini" @click="testConnection">测试连接</button>
      <text v-if="healthInfo" class="hint">{{ healthInfo }}</text>
    </view>

    <view class="section">
      <text class="label">人物性格</text>
      <picker :range="personaNames" :value="personaIndex" @change="onPersonaChange">
        <view class="picker-value">{{ personaNames[personaIndex] || '加载中...' }}</view>
      </picker>
    </view>

    <view v-if="modeOptions.length > 0" class="section">
      <text class="label">对话模式</text>
      <picker :range="modeOptions" :value="modeIndex" @change="onModeChange">
        <view class="picker-value">{{ modeOptions[modeIndex] || '自动' }}</view>
      </picker>
      <text class="hint">选「自动」时根据你的话术切换（如：害怕→哀求，留下→温柔）</text>
    </view>

    <view class="section">
      <text class="label">音色 ID（留空则按干员默认：蓝蒂 S_RUcfpOs32 / 浊心 S_SUcfpOs32）</text>
      <input
        class="input"
        v-model="voiceType"
        placeholder="留空使用干员默认音色"
        placeholder-class="placeholder"
      />
    </view>

    <view class="section">
      <text class="label">语速 {{ speed.toFixed(1) }}</text>
      <slider
        :value="speed * 100"
        min="80"
        max="150"
        step="5"
        activeColor="#e94560"
        @change="onSpeedChange"
      />
    </view>

    <view class="section actions">
      <button class="btn primary" @click="saveSettings">保存设置</button>
      <button class="btn warn" @click="clearChat">清空聊天记录</button>
    </view>
  </view>
</template>

<script>
import {
  setBaseUrl,
  healthCheck,
  fetchPersonas,
  isLocalhostUrl,
  isNativeMobileApp,
  formatNetworkError,
  normalizeBaseUrl,
  getBaseUrl
} from '@/api/client.js'
import { autoConfigureServer } from '@/utils/server-auto.js'
import { AUTO_SERVER_URL } from '@/config/server.js'
import { clearMessages } from '@/utils/audio.js'

export default {
  data() {
    return {
      serverBase: '',
      personaId: 'skadi',
      personas: [],
      personaIndex: 0,
      personaMode: 'auto',
      modeIndex: 0,
      voiceType: '',
      speed: 1.0,
      healthInfo: '',
      serverWarn: false,
      autoUrlHint: AUTO_SERVER_URL
    }
  },
  computed: {
    personaNames() {
      return this.personas.map((p) => p.name)
    },
    currentPersona() {
      return this.personas[this.personaIndex] || null
    },
    modeOptions() {
      const p = this.currentPersona
      if (!p || !p.modes || !p.modes.length) return []
      const labels = p.mode_labels || {}
      return ['自动', ...p.modes.map((m) => labels[m] || m)]
    },
    modeValues() {
      const p = this.currentPersona
      if (!p || !p.modes || !p.modes.length) return ['auto']
      return ['auto', ...p.modes]
    }
  },
  onShow() {
    autoConfigureServer(true)
    this.autoUrlHint = AUTO_SERVER_URL
    const raw = getBaseUrl() || uni.getStorageSync('server_base') || ''
    if (raw && !(isNativeMobileApp() && isLocalhostUrl(raw))) {
      this.serverBase = normalizeBaseUrl(raw)
      this.serverWarn = false
    } else {
      this.serverBase = ''
      this.serverWarn = isNativeMobileApp()
    }
    this.personaId = uni.getStorageSync('persona_id') || 'skadi'
    this.personaMode = uni.getStorageSync('persona_mode') || 'auto'
    this.voiceType = uni.getStorageSync('voice_type') || ''
    this.speed = parseFloat(uni.getStorageSync('tts_speed') || '1.0')
    this.loadPersonas()
  },
  methods: {
    async loadPersonas() {
      try {
        this.personas = await fetchPersonas()
        const idx = this.personas.findIndex((p) => p.id === this.personaId)
        this.personaIndex = idx >= 0 ? idx : 0
        this.syncModeIndex()
      } catch {
        this.personas = [
          { id: 'skadi', name: '斯卡蒂', modes: ['cold', 'vulnerable'], mode_labels: { cold: '冷淡戒备', vulnerable: '脆弱真心' } },
          { id: 'skadi_corrupting', name: '浊心斯卡蒂', modes: ['gentle', 'plead'], mode_labels: { gentle: '温柔占有', plead: '清醒哀求' } }
        ]
        this.syncModeIndex()
      }
    },
    syncModeIndex() {
      const idx = this.modeValues.indexOf(this.personaMode)
      this.modeIndex = idx >= 0 ? idx : 0
    },
    onPersonaChange(e) {
      this.personaIndex = Number(e.detail.value)
      this.personaMode = 'auto'
      this.modeIndex = 0
    },
    onModeChange(e) {
      this.modeIndex = Number(e.detail.value)
      this.personaMode = this.modeValues[this.modeIndex] || 'auto'
    },
    onSpeedChange(e) {
      this.speed = Number(e.detail.value) / 100
    },
    resetAutoServer() {
      autoConfigureServer(true)
      this.serverBase = getBaseUrl()
      this.serverWarn = false
      uni.showToast({ title: '已恢复自动地址', icon: 'success' })
    },
    async testConnection() {
      const target = normalizeBaseUrl(this.serverBase || AUTO_SERVER_URL)
      if (!target) {
        uni.showModal({ title: '地址无效', content: '请填写服务端地址', showCancel: false })
        return
      }
      try {
        this.serverBase = setBaseUrl(target)
        this.serverWarn = false
      } catch (e) {
        this.healthInfo = e.message || ''
        uni.showModal({ title: '地址无效', content: e.message, showCancel: false })
        return
      }
      uni.showLoading({ title: '测试中...' })
      try {
        const h = await healthCheck(true, true)
        let line = `${this.serverBase} | 已连接`
        line += ` | LLM:${h.llm_configured ? '✓' : '✗'} TTS:${h.tts_configured ? '✓' : '✗'}`
        if (h.tts_configured) {
          line += ` 鉴权:${h.tts_auth_ok ? '✓' : '✗'}`
        }
        line += ` ASR:${h.asr_enabled ? '开' : '关'}`
        if (h.tts_error) {
          line += `\n${String(h.tts_error).slice(0, 120)}`
        }
        this.healthInfo = line
        if (h.tts_configured && h.tts_auth_ok === false) {
          const isAuth = !!h.tts_auth_error
          const title = isAuth ? 'TTS 鉴权失败' : 'TTS 探测失败'
          const content = [
            h.tts_error || '',
            h.tts_hint || (isAuth ? '请检查 backend/.env 的 DOUBAO_API_KEY 并重启后端' : '请检查音色与 DOUBAO_CLONE_RESOURCE_ID 配置')
          ]
            .filter(Boolean)
            .join('\n\n')
            .slice(0, 400)
          uni.showModal({ title, content, showCancel: false })
        } else {
          uni.showToast({ title: '连接成功', icon: 'success' })
        }
      } catch (e) {
        const msg = formatNetworkError(e)
        this.healthInfo = `${this.serverBase} | 连接失败: ${msg}`
        uni.showModal({
          title: '连接失败',
          content: `${this.serverBase}\n\n${msg}`,
          showCancel: false
        })
      } finally {
        uni.hideLoading()
      }
    },
    saveSettings() {
      try {
        this.serverBase = setBaseUrl(this.serverBase)
        this.serverWarn = false
      } catch (e) {
        uni.showModal({ title: '无法保存', content: e.message, showCancel: false })
        return
      }
      const p = this.personas[this.personaIndex]
      if (p) {
        uni.setStorageSync('persona_id', p.id)
      }
      uni.setStorageSync('persona_mode', this.personaMode || 'auto')
      uni.setStorageSync('voice_type', this.voiceType)
      uni.setStorageSync('tts_speed', String(this.speed))
      uni.showToast({ title: '已保存', icon: 'success' })
    },
    clearChat() {
      uni.showModal({
        title: '确认',
        content: '清空所有干员的本地聊天记录？',
        success: (res) => {
          if (res.confirm) {
            clearMessages()
            uni.showToast({ title: '已清空', icon: 'success' })
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.page {
  padding: 32rpx;
  min-height: 100vh;
  background: #ededed;
}
.section {
  margin-bottom: 40rpx;
}
.label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 16rpx;
}
.input {
  background: #fff;
  border-radius: 8rpx;
  padding: 20rpx;
  color: #000;
  font-size: 28rpx;
  margin-bottom: 16rpx;
  border: 1rpx solid #e0e0e0;
}
.placeholder {
  color: #bbb;
}
.picker-value {
  background: #fff;
  padding: 20rpx;
  border-radius: 8rpx;
  color: #000;
  border: 1rpx solid #e0e0e0;
}
.btn {
  margin-top: 12rpx;
  background: #fff;
  color: #333;
}
.btn.primary {
  background: #07c160;
  color: #fff;
  width: 100%;
}
.btn.warn {
  background: #fff;
  color: #fa5151;
  width: 100%;
  margin-top: 16rpx;
  border: 1rpx solid #e0e0e0;
}
.warn-box {
  background: #fff3e0;
  border-radius: 8rpx;
  padding: 16rpx;
  margin-bottom: 12rpx;
  border: 1rpx solid #ffb74d;
}
.warn-text {
  font-size: 24rpx;
  color: #e65100;
  line-height: 1.5;
}
.hint {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #888;
}
.actions {
  margin-top: 48rpx;
}
</style>
