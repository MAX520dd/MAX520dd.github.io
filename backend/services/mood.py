"""开心度 / 好感度推理辅助与红包发放判定。"""

from __future__ import annotations

from typing import Any

from services.game_catalog import get_red_packet_for_persona, load_catalog

_POSITIVE_EMOTIONS = frozenset({"happy", "gentle"})
_NEGATIVE_EMOTIONS = frozenset({"cold", "sad", "melancholy", "possessive"})

# 红包（特殊礼物）触发：原 joy≥85 过严，多数对话达不到
_RED_PACKET_JOY_MIN: dict[str, int] = {
    "skadi": 72,
    "skadi_corrupting": 68,
}
_RED_PACKET_EMOTIONS: dict[str, frozenset[str]] = {
    "skadi": frozenset({"happy", "gentle", "calm", "melancholy"}),
    "skadi_corrupting": frozenset({"happy", "gentle", "calm", "possessive", "melancholy"}),
}

_EMOTION_WEIGHT = {
    "happy": 1.2,
    "gentle": 1.1,
    "calm": 1.0,
    "sad": 0.85,
    "melancholy": 0.85,
    "cold": 0.75,
    "possessive": 0.9,
}


def clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))


def adjust_mood_delta(raw_delta: int, emotion: str) -> int:
    w = _EMOTION_WEIGHT.get(emotion, 1.0)
    adjusted = int(round(raw_delta * w))
    if emotion in _POSITIVE_EMOTIONS and adjusted > 0:
        adjusted = min(10, adjusted + 1)
    if emotion in _NEGATIVE_EMOTIONS and adjusted > 0:
        adjusted = max(0, adjusted - 2)
    return clamp(adjusted, -10, 10)


def evaluate_red_packet_offer(
    persona_id: str,
    emotion: str,
    joy_before: int,
    mood_delta: int,
    last_red_packet_at: float | None,
    now_ts: float,
) -> dict[str, Any] | None:
    """
    服务端建议是否发放红包（客户端仍负责展示与领取）。
    joy_before: 客户端上报的开心度；用 mood_delta 预估本轮后 joy。
    """
    cfg = load_catalog()
    cooldown = int(cfg.get("red_packet_cooldown_sec") or 1800)
    if last_red_packet_at and (now_ts - last_red_packet_at) < cooldown:
        return None

    allowed = _RED_PACKET_EMOTIONS.get(persona_id, _POSITIVE_EMOTIONS)
    if emotion not in allowed:
        return None

    joy_min = _RED_PACKET_JOY_MIN.get(persona_id, 75)
    joy_after = clamp(joy_before + mood_delta)
    if joy_after < joy_min:
        return None

    # 平淡情绪需本轮明显回暖
    if emotion in ("calm", "melancholy", "possessive") and mood_delta < 3:
        return None

    packet = get_red_packet_for_persona(persona_id)
    if not packet:
        return None

    return {
        "item_id": packet["item_id"],
        "title": packet.get("title", "特殊红包"),
        "desc": packet.get("desc", ""),
        "icon": packet.get("icon", "🧧"),
        "persona_id": persona_id,
    }
