"""语境关怀送礼：博士诉说状态 → 角色按性格主动赠礼。"""

from __future__ import annotations

from typing import Any

from services.game_catalog import load_catalog
from services.mood import clamp

_CARING_EMOTIONS: dict[str, frozenset[str]] = {
    "skadi": frozenset({"gentle", "happy", "calm", "melancholy"}),
    "skadi_corrupting": frozenset({"gentle", "happy", "calm", "melancholy", "possessive"}),
}


def _cfg() -> dict[str, Any]:
    return load_catalog().get("contextual_gifts") or {}


def _settings() -> dict[str, Any]:
    return _cfg().get("settings") or {}


def detect_scenario(user_text: str) -> str | None:
    """从博士本轮发言匹配关怀场景（饿、累、冷、不适等）。"""
    t = (user_text or "").strip()
    if not t:
        return None
    scenarios = _cfg().get("scenarios") or {}
    best_id: str | None = None
    best_len = 0
    for scenario_id, scenario in scenarios.items():
        for trigger in scenario.get("triggers") or []:
            trig = (trigger or "").strip()
            if trig and trig in t and len(trig) > best_len:
                best_id = scenario_id
                best_len = len(trig)
    return best_id


def _gift_def(scenario_id: str, persona_id: str) -> dict[str, Any] | None:
    scenario = (_cfg().get("scenarios") or {}).get(scenario_id) or {}
    gift = (scenario.get("gifts") or {}).get(persona_id)
    return dict(gift) if gift else None


def precheck_contextual_gift(
    persona_id: str,
    scenario_id: str,
    affection: int,
    joy: int,
    last_trigger_at: float | None,
    now_ts: float,
) -> dict[str, Any] | None:
    """
    对话前：好感/开心度/冷却达标则注入互动 prompt。
    不在此阶段发礼物，等 LLM 情绪确认后再 finalize。
    """
    gift = _gift_def(scenario_id, persona_id)
    if not gift:
        return None

    settings = _settings()
    cooldown = int(settings.get("cooldown_sec") or 2400)
    if last_trigger_at and (now_ts - last_trigger_at) < cooldown:
        return None

    aff_min = int(settings.get("affection_min") or 55)
    joy_min = int(settings.get("joy_min") or 38)
    if affection < aff_min or joy < joy_min:
        return None

    hint = (gift.get("system_hint") or "").strip()
    if not hint:
        return None

    return {
        "scenario_id": scenario_id,
        "persona_id": persona_id,
        "system_hint": hint,
        "item_id": gift.get("item_id", f"{persona_id}_{scenario_id}"),
        "title": gift.get("title", "关怀"),
        "desc": gift.get("desc", ""),
        "icon": gift.get("icon", "🎁"),
        "reward_orundum": int(gift.get("reward_orundum") or 35),
        "narrative": gift.get("narrative", ""),
    }


def finalize_contextual_gift(
    pre: dict[str, Any],
    emotion: str,
    mood_delta: int,
) -> dict[str, Any] | None:
    """对话后：情绪足够温软才真正送礼。"""
    persona_id = pre.get("persona_id") or ""
    allowed = _CARING_EMOTIONS.get(persona_id, frozenset({"gentle", "happy", "calm"}))
    if emotion not in allowed:
        return None
    if emotion in ("cold", "sad") and mood_delta < 1:
        return None
    if emotion in ("calm", "melancholy", "possessive") and mood_delta < 2:
        return None

    return {
        "gift_type": "contextual",
        "scenario_id": pre.get("scenario_id"),
        "item_id": pre["item_id"],
        "title": pre.get("title", "关怀"),
        "desc": pre.get("desc", ""),
        "icon": pre.get("icon", "🎁"),
        "reward_orundum": pre.get("reward_orundum", 35),
        "narrative": pre.get("narrative", ""),
        "persona_id": persona_id,
    }
