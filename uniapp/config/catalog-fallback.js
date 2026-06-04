/**
 * 后端 /v1/game/catalog 不可用时的展示用兜底（仅 shop_items 展示字段）。
 * 完整配置仍以 backend/data/game_catalog.json 为准。
 */
export const CATALOG_FALLBACK = {
  claim_reward_orundum: 600,
  red_packet_cooldown_sec: 1800,
  shop_items: [
    {
      id: 'gift_saltwind_memory',
      name: '盐风城回忆',
      desc: '送给斯卡蒂，她会向博士讲述盐风城的往事，并附上一张照片。',
      icon: '🏛️',
      price: 480,
      target_persona_id: 'skadi',
      event_type: 'story_photo'
    },
    {
      id: 'gift_azure_tide',
      name: '幽蓝潮声',
      desc: '送给浊心斯卡蒂，她会为博士唱一首四句短歌（潮汐主题）。',
      icon: '🎵',
      price: 520,
      target_persona_id: 'skadi_corrupting',
      event_type: 'sing'
    },
    {
      id: 'gift_greatsea_slumber',
      name: '大海之眠',
      desc: '送给浊心斯卡蒂，她会困倦地回应，并发出轻轻的呼噜声。',
      icon: '💤',
      price: 450,
      target_persona_id: 'skadi_corrupting',
      event_type: 'drowsy_snore'
    }
  ],
  special_item_meta: {}
}
