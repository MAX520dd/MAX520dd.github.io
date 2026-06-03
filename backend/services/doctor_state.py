"""博士状态：仅在 LLM 推理时作为情境约束，不生成「状态观察」类对白。"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from config import BASE_DIR

_DATA_PATH = BASE_DIR / "data" / "doctor_states.json"

# 多维度异常时，优先纳入推理的情境（靠前越优先）
_DIM_PRIORITY = (
    "injury",
    "mentalState",
    "sanity",
    "fatigue",
    "sleep",
    "stress",
    "dutyStatus",
)


@lru_cache(maxsize=1)
def load_doctor_state_config() -> dict[str, Any]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_defaults() -> dict[str, str]:
    return dict(load_doctor_state_config().get("defaults") or {})


def get_dimensions() -> list[dict[str, Any]]:
    return list(load_doctor_state_config().get("dimensions") or [])


def normalize_doctor_state(raw: dict[str, Any] | None) -> dict[str, str]:
    defaults = get_defaults()
    out = dict(defaults)
    if not raw:
        return out
    valid_keys = {d["key"] for d in get_dimensions()}
    for k, v in raw.items():
        if k in valid_keys and v is not None and str(v).strip():
            out[k] = str(v).strip()
    return out


def _observation_for(persona_id: str, dim_key: str, value: str) -> str:
    cfg = load_doctor_state_config()
    obs_map = (cfg.get("observations") or {}).get(persona_id) or {}
    dim_obs = obs_map.get(dim_key) or {}
    return dim_obs.get(value) or ""


def _delta_dimensions(state: dict[str, str]) -> list[tuple[str, str, str]]:
    """返回 (key, label, value) 列表，仅含与默认不同的维度，按优先级排序。"""
    defaults = get_defaults()
    label_by_key = {d["key"]: d.get("label", d["key"]) for d in get_dimensions()}
    deltas: list[tuple[str, str, str]] = []
    for key in _DIM_PRIORITY:
        val = state.get(key, defaults.get(key, ""))
        if val != defaults.get(key, ""):
            deltas.append((key, label_by_key.get(key, key), val))
    for dim in get_dimensions():
        key = dim["key"]
        if key in _DIM_PRIORITY:
            continue
        val = state.get(key, defaults.get(key, ""))
        if val != defaults.get(key, ""):
            deltas.append((key, dim.get("label", key), val))
    return deltas


def build_doctor_state_block(persona_id: str, doctor_state: dict[str, Any] | None) -> str:
    """
    生成注入 system 的推理情境（非对白脚本）。
    全部为默认时不注入，避免无意义的「特殊对话」倾向。
    """
    if doctor_state is None:
        return ""

    state = normalize_doctor_state(doctor_state)
    deltas = _delta_dimensions(state)
    if not deltas:
        return ""

    facts = "，".join(f"{label}{value}" for _, label, value in deltas)

    notes: list[str] = []
    for key, _, value in deltas[:4]:
        obs = _observation_for(persona_id, key, value)
        if obs:
            notes.append(obs)

    lines = [
        "【博士情境·仅供推理】",
        "以下为博士当前客观档案与你在本角色视角下的内心把握。用于决定语气、急缓、是否劝阻或担心；"
        "不得写入可口说对白，不得向博士汇报或列举这些条目，不得使用「观察」「状态」「检测」等元话术。",
        f"相对常态的变化：{facts}。",
    ]
    if notes:
        lines.append(f"内心把握（勿照读）：{' '.join(notes)}")
    lines.append(
        "回复时仅在与博士本条消息自然相关时，隐含体现上述情境；无关时不要主动提起伤势、神志等。"
    )
    return "\n".join(lines)


def public_meta() -> dict[str, Any]:
    cfg = load_doctor_state_config()
    return {
        "defaults": get_defaults(),
        "dimensions": get_dimensions(),
    }
