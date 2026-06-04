"""表情包发送时机判定与人设池。"""

from __future__ import annotations

import random
from typing import Any

from services.game_catalog import load_catalog


def _persona_settings(persona_id: str) -> dict[str, Any]:
    cfg = load_catalog()
    settings = (cfg.get("sticker_settings") or {}).get(persona_id) or {}
    defaults = {
        "skadi": {
            "cooldown_sec": 180,
            "min_joy": 35,
            "pity_every": 5,
            "base_probability": 0.14,
            "emotion_weights": {
                "cold": 1.25,
                "calm": 1.05,
                "sad": 1.1,
                "melancholy": 1.0,
                "gentle": 0.75,
                "happy": 0.7,
            },
        },
        "skadi_corrupting": {
            "cooldown_sec": 150,
            "min_joy": 30,
            "pity_every": 4,
            "base_probability": 0.18,
            "emotion_weights": {
                "gentle": 1.2,
                "possessive": 1.15,
                "melancholy": 1.05,
                "calm": 1.0,
                "sad": 0.95,
                "happy": 1.1,
                "cold": 0.5,
            },
        },
    }
    base = defaults.get(persona_id, {"cooldown_sec": 240, "min_joy": 40, "base_probability": 0.1})
    return {**base, **settings}


def _pick_sticker(persona_id: str, emotion: str) -> dict[str, Any] | None:
    packs = (load_catalog().get("sticker_packs") or {}).get(persona_id) or {}
    pool = list(packs.get(emotion) or [])
    if not pool and emotion not in packs:
        pool = list(packs.get("calm") or packs.get("gentle") or [])
    if not pool:
        for items in packs.values():
            if items:
                pool.extend(items)
    if not pool:
        return None
    item = random.choice(pool)
    cfg = load_catalog()
    folders = cfg.get("sticker_image_folders") or {}
    folder = folders.get(persona_id, "")
    image_file = (item.get("image") or item.get("image_file") or "").strip()
    image_url = ""
    if image_file and folder:
        image_url = f"/static/biaoqingbao/{folder}/{image_file}"
    return {
        "sticker_id": item.get("id", "sticker"),
        "emoji": item.get("emoji", ""),
        "caption": item.get("caption", ""),
        "image_url": image_url or item.get("image_url", ""),
    }


def _user_turn_index(history: list[dict[str, str]] | None) -> int:
    """当前轮为第几次用户发言（含本轮）。"""
    if not history:
        return 1
    n = sum(1 for h in history if h.get("role") == "user")
    return max(1, n + 1)


def evaluate_sticker_offer(
    persona_id: str,
    emotion: str,
    mood_delta: int,
    joy_before: int,
    last_sticker_at: float | None,
    now_ts: float,
    *,
    red_packet_this_turn: bool = False,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    """
    服务端判定是否在本轮追加表情包（客户端负责展示）。
    频率因人设而异：蓝蒂更克制，浊心略高但仍受冷却限制。
    """
    if red_packet_this_turn:
        return None

    settings = _persona_settings(persona_id)
    cooldown = int(settings.get("cooldown_sec") or 240)
    if last_sticker_at and (now_ts - last_sticker_at) < cooldown:
        return None

    if joy_before < int(settings.get("min_joy") or 40):
        return None

    turn_idx = _user_turn_index(history)
    pity_every = int(settings.get("pity_every") or 0)
    if pity_every > 0 and turn_idx % pity_every == 0:
        picked = _pick_sticker(persona_id, emotion)
        if picked:
            return {**picked, "persona_id": persona_id, "emotion": emotion}

    weights = settings.get("emotion_weights") or {}
    w = float(weights.get(emotion, 0.85))
    if w <= 0:
        return None

    p = float(settings.get("base_probability") or 0.1) * w
    if mood_delta >= 4:
        p *= 1.35
    elif mood_delta >= 2:
        p *= 1.15
    elif mood_delta <= -3:
        p *= 0.35
    elif mood_delta < 0:
        p *= 0.65

    if joy_before >= 70:
        p *= 1.12
    elif joy_before <= 45:
        p *= 0.85

    p = min(0.42, max(0.03, p))
    if random.random() >= p:
        return None

    picked = _pick_sticker(persona_id, emotion)
    if not picked:
        return None

    return {
        **picked,
        "persona_id": persona_id,
        "emotion": emotion,
    }
