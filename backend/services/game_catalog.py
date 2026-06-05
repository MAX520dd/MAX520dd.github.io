"""商城、红包、特殊物品目录。"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from config import BASE_DIR

_CATALOG_PATH = BASE_DIR / "data" / "game_catalog.json"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_shop_item(item_id: str) -> dict[str, Any] | None:
    for item in load_catalog().get("shop_items") or []:
        if item.get("id") == item_id:
            return item
    return None


def get_red_packet_for_persona(persona_id: str) -> dict[str, Any] | None:
    rp = (load_catalog().get("red_packets") or {}).get(persona_id)
    if not rp:
        return None
    return {**rp, "persona_id": persona_id}


def get_special_item_meta(item_id: str) -> dict[str, Any] | None:
    meta = (load_catalog().get("special_item_meta") or {}).get(item_id)
    return dict(meta) if meta else None


def public_catalog() -> dict[str, Any]:
    cfg = load_catalog()
    return {
        "claim_reward_orundum": cfg.get("claim_reward_orundum", 600),
        "red_packet_cooldown_sec": cfg.get("red_packet_cooldown_sec", 1800),
        "red_packets": cfg.get("red_packets") or {},
        "shop_items": cfg.get("shop_items") or [],
        "special_item_meta": cfg.get("special_item_meta") or {},
        "easter_eggs": cfg.get("easter_eggs") or {},
        "contextual_gifts": cfg.get("contextual_gifts") or {},
        "sticker_settings": cfg.get("sticker_settings") or {},
        "sticker_packs": cfg.get("sticker_packs") or {},
    }
