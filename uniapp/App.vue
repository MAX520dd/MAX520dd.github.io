<script>
import { autoConfigureServer } from '@/utils/server-auto.js'

export default {
  onLaunch() {
    autoConfigureServer(true)
    if (!uni.getStorageSync('persona_id')) {
      uni.setStorageSync('persona_id', 'skadi_corrupting')
    }
    if (!uni.getStorageSync('persona_mode')) {
      uni.setStorageSync('persona_mode', 'auto')
    }
    // 音色留空则使用各干员 personas.json 中的 default_voice
    // 旧版曾全局写入浊心音色，清除后蓝蒂/浊心才能各用各的 default_voice
    if (uni.getStorageSync('voice_type') === 'S_SUcfpOs32') {
      uni.removeStorageSync('voice_type')
    }
  }
}
</script>

<style>
page {
  background-color: #ededed;
  color: #000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}
</style>
