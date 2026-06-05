"""对话彩蛋：关键词触发特殊礼物与互动。"""

from __future__ import annotations

import re
from typing import Any

from services.game_catalog import load_catalog

_FULLWIDTH_TRANS = str.maketrans("Ｖｖ５０ＫＦＣ", "Vv50KFC")
_VME50_RE = re.compile(r"(?:v|微)\s*我\s*(?:50|五十)", re.IGNORECASE)
_KFC_RE = re.compile(r"kfc|肯德基|肯德鸡", re.IGNORECASE)
_THURSDAY_TOKENS = ("星期四", "周四", "礼拜四", "疯狂星期四")


def _normalize_easter_text(user_text: str) -> str:
    return (user_text or "").strip().translate(_FULLWIDTH_TRANS)


# 三组关键词，命中至少 2 组即触发（「疯狂星期四」梗句单独也算触发）
def _group_hits(t: str) -> int:
    hits = 0
    if _KFC_RE.search(t):
        hits += 1
    if _VME50_RE.search(t):
        hits += 1
    if any(k in t for k in _THURSDAY_TOKENS):
        hits += 1
    return hits

CRAZY_THURSDAY_SYSTEM = (
    "【隐藏彩蛋·疯狂星期四】博士在玩「疯狂星期四 / V我50 / 肯德基」梗。\n"
    "你是主线蓝蒂：先冷淡装不懂（一句），再别扭地认输，像把私房钱塞给博士（一句）。"
    "可提五十、炸鸡、星期四，但保持猎手人设，不要活泼玩梗腔，不要列清单。\n"
    "≤80字，<cot> 格式，末行 [emotion:gentle] 或 [emotion:calm]，可加 [mood_delta:+5]。"
)


def crazy_thursday_keyword_hits(user_text: str) -> int:
    t = _normalize_easter_text(user_text)
    if not t:
        return 0
    return _group_hits(t)


def is_crazy_thursday_request(user_text: str) -> bool:
    t = _normalize_easter_text(user_text)
    if not t:
        return False
    # 梗句本身即完整触发，不必再凑第二组词
    if "疯狂星期四" in t:
        return True
    return _group_hits(t) >= 2


def _easter_cfg(egg_id: str) -> dict[str, Any]:
    return (load_catalog().get("easter_eggs") or {}).get(egg_id) or {}


def evaluate_crazy_thursday_offer(
    persona_id: str,
    user_text: str,
    last_trigger_at: float | None,
    now_ts: float,
) -> dict[str, Any] | None:
    """蓝蒂专属：疯狂星期四梗 → 50 合成玉礼物 + 互动对白。"""
    if persona_id != "skadi":
        return None
    if not is_crazy_thursday_request(user_text):
        return None

    cfg = _easter_cfg("crazy_thursday")
    cooldown = int(cfg.get("cooldown_sec") or 86400)
    if last_trigger_at and (now_ts - last_trigger_at) < cooldown:
        return None

    return {
        "egg_id": "crazy_thursday",
        "item_id": cfg.get("item_id", "skadi_crazy_thursday"),
        "title": cfg.get("title", "疯狂星期四·50"),
        "desc": cfg.get("desc", "斯卡蒂塞给你的五十。"),
        "icon": cfg.get("icon", "🍗"),
        "reward_orundum": int(cfg.get("reward_orundum") or 50),
        "narrative": cfg.get("narrative", ""),
        "persona_id": persona_id,
    }
