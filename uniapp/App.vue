<script>
import { autoConfigureServer } from '@/utils/server-auto.js'

export default {
  onLaunch() {
    autoConfigureServer(false)
    if (!uni.getStorageSync('persona_id')) {
      uni.setStorageSync('persona_id', 'skadi_corrupting')
    }
    if (!uni.getStorageSync('persona_mode')) {
      uni.setStorageSync('persona_mode', 'auto')
    }
    // 一次性迁移：旧版曾全局写入浊心音色，清除后各干员才用 personas.json 的 default_voice
    if (
      !uni.getStorageSync('voice_type_migrated_v1') &&
      uni.getStorageSync('voice_type') === 'S_SUcfpOs32'
    ) {
      uni.removeStorageSync('voice_type')
      uni.setStorageSync('voice_type_migrated_v1', '1')
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
