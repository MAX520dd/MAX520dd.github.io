/**
 * 本地表情包资源（uniapp/static/biaoqingbao）
 * skd → 蓝蒂 skadi；zhuoxinskd → 浊心 skadi_corrupting
 */

export const STICKER_IMAGE_FOLDERS = {
  skadi: 'skd',
  skadi_corrupting: 'zhuoxinskd'
}

/** 与 backend game_catalog sticker id 对应 */
export const STICKER_LOCAL_ASSETS = {
  skadi_corrupting: [
    {
      id: 'cor_tide',
      file: '64ebcdaeb9ed3a017891d21b4dc5c509.jpg',
      caption: '潮声'
    },
    {
      id: 'cor_heart',
      file: '69fdc17c2614c30bd7ede98b9e614d1a.jpg',
      caption: '博士'
    },
    {
      id: 'cor_hum',
      file: '4d6c6e912032746af1e3e3ea01f9061f.jpg',
      caption: '哼给你'
    },
    {
      id: 'cor_hold',
      file: '787df6baca1d70e53c871b4d7225b761.jpg',
      caption: '别走'
    },
    {
      id: 'cor_eye',
      file: 'ad5a84a972e3122ee3fed71bf8b9b038.jpg',
      caption: '只看你'
    },
    {
      id: 'cor_sleepy',
      file: 'ad5a84a972e3122ee3fed71bf8b9b038.jpg',
      caption: '安静'
    },
    {
      id: 'cor_mist',
      file: '787df6baca1d70e53c871b4d7225b761.jpg',
      caption: '像梦'
    },
    {
      id: 'cor_shine',
      file: '69fdc17c2614c30bd7ede98b9e614d1a.jpg',
      caption: '开心'
    }
  ],
  skadi: []
}

export function stickerStaticPath(personaId, file) {
  const folder = STICKER_IMAGE_FOLDERS[personaId]
  if (!folder || !file) return ''
  return `/static/biaoqingbao/${folder}/${file}`
}

/**
 * 将服务端 sticker_offer 解析为 App 内可显示的本地图片路径。
 */
export function resolveStickerImageUrl(personaId, offer) {
  if (!offer) return ''
  const raw = offer.image_url || offer.imageUrl || ''
  if (raw.startsWith('/static/')) return raw
  const pid = offer.persona_id || personaId
  const sid = offer.sticker_id || ''
  const list = STICKER_LOCAL_ASSETS[pid] || []
  const hit = list.find((x) => x.id === sid)
  if (hit?.file) return stickerStaticPath(pid, hit.file)
  if (list.length && sid) {
    const idx =
      Math.abs(
        sid.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
      ) % list.length
    return stickerStaticPath(pid, list[idx].file)
  }
  return ''
}

export function enrichStickerFromOffer(personaId, offer) {
  if (!offer) return null
  const imageUrl = resolveStickerImageUrl(personaId, offer)
  if (!imageUrl && !offer.emoji) return null
  return {
    stickerId: offer.sticker_id || 'sticker',
    emoji: offer.emoji || '',
    caption: offer.caption || '',
    imageUrl,
    personaId: offer.persona_id || personaId
  }
}
