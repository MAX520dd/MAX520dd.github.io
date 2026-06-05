import { enrichStickerFromOffer } from '@/utils/sticker-images.js'

const GAME_KEY = 'game_state_v1'
const REL_PREFIX = 'relation_'

const DEFAULT_WALLET = { orundum: 1200 }

const DEFAULT_RELATION = {
  affection: 100,
  joy: 50,
  lastRedPacketAt: 0,
  lastCrazyThursdayAt: 0,
  lastContextualGiftAt: 0,
  lastStickerAt: 0,
  lastMoodDelta: 0
}

function readGame() {
  try {
    return uni.getStorageSync(GAME_KEY) || {}
  } catch {
    return {}
  }
}

function writeGame(state) {
  uni.setStorageSync(GAME_KEY, state)
}

function clamp(n, lo = 0, hi = 100) {
  return Math.max(lo, Math.min(hi, Math.round(n)))
}

export function getWallet() {
  const g = readGame()
  return { ...DEFAULT_WALLET, ...(g.wallet || {}) }
}

export function addOrundum(amount) {
  const g = readGame()
  g.wallet = { ...DEFAULT_WALLET, ...(g.wallet || {}) }
  g.wallet.orundum = Math.max(0, (g.wallet.orundum || 0) + amount)
  writeGame(g)
  return g.wallet.orundum
}

export function getInventory() {
  const g = readGame()
  return Array.isArray(g.inventory) ? g.inventory : []
}

function setInventory(list) {
  const g = readGame()
  g.inventory = list
  writeGame(g)
}

export function getSpecialItems() {
  const g = readGame()
  return Array.isArray(g.specialItems) ? g.specialItems : []
}

function addSpecialItem(entry) {
  const g = readGame()
  const list = Array.isArray(g.specialItems) ? g.specialItems : []
  if (!list.some((x) => x.itemId === entry.itemId && x.claimedAt === entry.claimedAt)) {
    list.unshift(entry)
  }
  g.specialItems = list.slice(0, 100)
  writeGame(g)
}

export function getRelation(personaId) {
  const g = readGame()
  const key = REL_PREFIX + personaId
  return { ...DEFAULT_RELATION, ...(g[key] || {}) }
}

function saveRelation(personaId, rel) {
  const g = readGame()
  g[REL_PREFIX + personaId] = rel
  writeGame(g)
}

function pickChatGiftOffer(easterEggOffer, contextualGiftOffer, redPacketOffer) {
  if (easterEggOffer && easterEggOffer.item_id) {
    return { offer: easterEggOffer, source: 'easter_egg' }
  }
  if (contextualGiftOffer && contextualGiftOffer.item_id) {
    return { offer: contextualGiftOffer, source: 'contextual_gift' }
  }
  if (redPacketOffer && redPacketOffer.item_id) {
    return { offer: redPacketOffer, source: 'red_packet' }
  }
  return null
}

export function applyMoodFromChat(
  personaId,
  moodDelta,
  emotion,
  serverOffer,
  joyAfter,
  affectionAfter,
  stickerOffer,
  easterEggOffer,
  contextualGiftOffer
) {
  const rel = getRelation(personaId)
  const delta = Number(moodDelta) || 0
  if (joyAfter != null) rel.joy = clamp(joyAfter)
  else rel.joy = clamp(rel.joy + delta)
  if (affectionAfter != null) rel.affection = clamp(affectionAfter)
  else rel.affection = clamp(rel.affection + Math.round(delta * 0.6))
  rel.lastMoodDelta = delta
  saveRelation(personaId, rel)

  let packet = null
  let narrative = ''
  const picked = pickChatGiftOffer(easterEggOffer, contextualGiftOffer, serverOffer)
  if (picked) {
    const { offer, source } = picked
    const reward =
      source === 'red_packet' ? undefined : Number(offer.reward_orundum) || (source === 'easter_egg' ? 50 : 35)
    packet = {
      id: Date.now() + Math.random(),
      itemId: offer.item_id,
      title:
        offer.title ||
        (source === 'easter_egg' ? '疯狂星期四·V我50' : source === 'contextual_gift' ? '关怀' : '特殊红包'),
      desc: offer.desc || '',
      icon: offer.icon || (source === 'easter_egg' ? '🍗' : source === 'contextual_gift' ? '🎁' : '🧧'),
      rewardOrundum: reward,
      source,
      personaId,
      claimed: false
    }
    if (source === 'easter_egg' || source === 'contextual_gift') {
      narrative = offer.narrative || ''
    }
    if (source === 'easter_egg') {
      rel.lastCrazyThursdayAt = Date.now() / 1000
    } else if (source === 'contextual_gift') {
      rel.lastContextualGiftAt = Date.now() / 1000
    } else {
      rel.lastRedPacketAt = Date.now() / 1000
    }
    saveRelation(personaId, rel)
  }

  let sticker = enrichStickerFromOffer(personaId, stickerOffer)
  if (sticker) {
    sticker = { id: Date.now() + Math.random(), ...sticker, personaId }
    rel.lastStickerAt = Date.now() / 1000
    saveRelation(personaId, rel)
  }

  return { relation: rel, redPacket: packet, sticker, narrative }
}

export function canOfferRedPacketLocally(personaId) {
  const rel = getRelation(personaId)
  const g = readGame()
  const cooldown = (g.redPacketCooldownSec || 1800) * 1000
  if (rel.lastRedPacketAt && Date.now() - rel.lastRedPacketAt * 1000 < cooldown) {
    return false
  }
  const joyMin = personaId === 'skadi' ? 72 : 68
  return rel.joy >= joyMin
}

export function claimRedPacket(packet, rewardOrundum = 600) {
  if (!packet || packet.claimed) {
    return { ok: false, message: '已领取' }
  }
  const amount = packet.rewardOrundum ?? rewardOrundum
  const orundum = addOrundum(amount)
  addSpecialItem({
    itemId: packet.itemId,
    title: packet.title,
    icon: packet.icon,
    source: packet.source || 'red_packet',
    personaId: packet.personaId,
    claimedAt: Date.now()
  })
  return { ok: true, orundum, reward: amount }
}

export function buyShopItem(item, catalog) {
  const price = item.price || 0
  const wallet = getWallet()
  if (wallet.orundum < price) {
    return { ok: false, message: '合成玉不足' }
  }
  const g = readGame()
  g.wallet = { ...wallet, orundum: wallet.orundum - price }
  const inv = getInventory()
  const row = inv.find((x) => x.itemId === item.id)
  if (row) row.count += 1
  else inv.push({ itemId: item.id, count: 1 })
  g.inventory = inv
  if (catalog?.red_packet_cooldown_sec) {
    g.redPacketCooldownSec = catalog.red_packet_cooldown_sec
  }
  writeGame(g)
  return { ok: true, orundum: g.wallet.orundum }
}

export function consumeInventoryItem(itemId) {
  const inv = getInventory()
  const row = inv.find((x) => x.itemId === itemId)
  if (!row || row.count < 1) {
    return false
  }
  row.count -= 1
  setInventory(inv.filter((x) => x.count > 0))
  return true
}

export function getInventoryCount(itemId) {
  const row = getInventory().find((x) => x.itemId === itemId)
  return row ? row.count : 0
}

export function cacheCatalog(catalog) {
  const g = readGame()
  g.catalogCache = catalog
  if (catalog?.claim_reward_orundum) {
    g.claimRewardOrundum = catalog.claim_reward_orundum
  }
  if (catalog?.red_packet_cooldown_sec) {
    g.redPacketCooldownSec = catalog.red_packet_cooldown_sec
  }
  writeGame(g)
}

export function getCachedCatalog() {
  return readGame().catalogCache || null
}

export function clearCatalogCache() {
  const g = readGame()
  delete g.catalogCache
  writeGame(g)
}

export function getClaimRewardOrundum() {
  const g = readGame()
  return g.claimRewardOrundum || 600
}

export function recordGiftSpecialItem(itemId, meta) {
  addSpecialItem({
    itemId,
    title: meta?.name || itemId,
    icon: meta?.icon || '🎁',
    source: 'gift',
    claimedAt: Date.now()
  })
}

export function setPendingGiftEvent(personaId, event) {
  const g = readGame()
  g['pending_gift_' + personaId] = event
  writeGame(g)
}

export function consumePendingGiftEvent(personaId) {
  const g = readGame()
  const key = 'pending_gift_' + personaId
  const ev = g[key]
  if (ev) {
    delete g[key]
    writeGame(g)
  }
  return ev || null
}
