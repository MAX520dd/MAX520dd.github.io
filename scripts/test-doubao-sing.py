#!/usr/bin/env python3
"""实测豆包 V3 emotion=sing（需 backend/.env 中 DOUBAO_API_KEY）。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from services import tts_doubao  # noqa: E402


async def main() -> None:
    text = "小星星，亮晶晶，挂在天上放光明"
    print("=== 1. 官方 emotion=sing（灿灿 + seed-tts-2.0）===")
    try:
        r = await tts_doubao.synthesize_official_sing(text)
        print("OK", r.get("audio_path"), "bytes?", Path(r["audio_path"]).stat().st_size)
        print("mode", r.get("sing_mode"))
    except Exception as e:
        print("FAIL", e)

    print("\n=== 2. 复刻音色 S_ + sing（预期失败或仅朗读）===")
    voice = "S_SUcfpOs32"
    try:
        from config import settings

        r2 = await tts_doubao.synthesize_official_sing(text, voice_type=voice)
        print("unexpected OK", r2.get("audio_path"))
    except ValueError as e:
        print("expected:", e)


if __name__ == "__main__":
    asyncio.run(main())
