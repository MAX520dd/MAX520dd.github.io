"""商城赠礼触发的特殊事件（LLM + TTS）。"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from openai import OpenAI

from config import settings
from services.game_catalog import get_shop_item
from services.persona import (
    get_persona,
    parse_emotion_and_clean,
    parse_mood_delta,
    prepare_tts_text,
    strip_paren_from_raw,
    extract_stage_directions,
    emotion_context_for_tts,
    speed_for_emotion,
)
from services import tts_doubao


def _client() -> OpenAI:
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)


def _llm_event(system: str, user: str) -> str:
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置")
    resp = _client().chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.85,
        max_tokens=280,
        top_p=settings.llm_top_p,
        extra_body={"think": False},
    )
    return (resp.choices[0].message.content or "").strip()


SING_COT_HINT = "用轻柔、缓慢、带摇篮曲旋律感的语气哼唱歌谣"

# 排障见 docs/doubao-tts-setup.md → https://www.volcengine.com/docs/6561/162929?lang=zh


def _flatten_lyrics_for_tts(text: str) -> str:
    """哼唱 TTS：多行歌词合并为一行，避免流式合成断句突兀。"""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) <= 1:
        return text.strip()
    return "，".join(lines)


async def _try_tts(**kwargs: Any) -> dict[str, Any] | None:
    """TTS 失败时不中断赠礼，仅省略语音。"""
    try:
        return await tts_doubao.synthesize(**kwargs)
    except ValueError as e:
        logger.warning("gift TTS skipped: %s", e)
        return None


async def _require_tts(retries: int = 2, **kwargs: Any) -> dict[str, Any]:
    """歌谣等必须带语音的赠礼：失败则抛错，避免「只有文字、没有歌」。"""
    last_err: ValueError | None = None
    for attempt in range(max(1, retries)):
        try:
            res = await tts_doubao.synthesize(**kwargs)
            if res.get("audio_url"):
                return res
            last_err = ValueError("TTS 未返回音频地址")
        except ValueError as e:
            last_err = e
            logger.warning("gift TTS attempt %s failed: %s", attempt + 1, e)
    msg = str(last_err) if last_err else "TTS 合成失败"
    raise ValueError(
        f"歌谣语音合成失败：{msg}。请检查 backend/.env 中 DOUBAO_API_KEY、"
        "DOUBAO_CLONE_RESOURCE_ID=seed-icl-2.0、DOUBAO_TTS_MODEL=seed-tts-2.0-expressive；"
        "排障文档见 docs/doubao-tts-setup.md（火山官方 https://www.volcengine.com/docs/6561/162929?lang=zh ）"
    ) from last_err


def _absolute_url(path: str) -> str:
    if not path:
        return ""
    if path.startswith("http"):
        return path
    base = (settings.public_base_url or "").rstrip("/")
    return f"{base}{path}" if base else path


async def trigger_gift_event(persona_id: str, item_id: str) -> dict[str, Any]:
    item = get_shop_item(item_id)
    if not item:
        raise ValueError(f"未知道具: {item_id}")
    if item.get("target_persona_id") != persona_id:
        raise ValueError(f"该礼物只能送给指定干员")

    persona = get_persona(persona_id)
    if not persona:
        raise ValueError(f"未找到人物: {persona_id}")

    event_type = item.get("event_type", "")
    system = f"{persona['system_prompt']}\n\n【特殊事件·赠礼】\n{item.get('event_prompt', '')}"
    user = item.get("user_trigger", "博士送来了礼物。")
    raw = _llm_event(system, user)

    voice = persona.get("default_voice", settings.doubao_voice_type)
    base_speed = float(persona.get("default_speed", 1.0))

    result: dict[str, Any] = {
        "event_type": event_type,
        "item_id": item_id,
        "persona_id": persona_id,
        "persona_name": persona.get("name", ""),
        "reply_text": "",
        "stage_direction": "",
        "emotion": "calm",
        "audio_url": "",
        "audio_url_snore": "",
        "image_url": "",
        "duration_sec": 0,
        "default_voice": voice,
    }

    if event_type == "story_photo":
        _, body = parse_mood_delta(raw)
        reply, emotion, tts_speech, cot_hint = parse_emotion_and_clean(body)
        result["reply_text"] = reply
        result["emotion"] = emotion
        result["stage_direction"] = extract_stage_directions(body, emotion)
        img_path = item.get("placeholder_image", "")
        result["image_url"] = _absolute_url(img_path)
        if tts_speech.strip():
            tts_text = prepare_tts_text(
                strip_paren_from_raw(tts_speech), emotion, voice, cot_hint
            )
            spd = speed_for_emotion(base_speed, emotion)
            tts_res = await _try_tts(
                text=tts_text,
                voice_type=voice,
                speed=spd,
                emotion=emotion,
                context_text=result["stage_direction"],
            )
            if tts_res:
                result["audio_url"] = tts_res["audio_url"]
                result["duration_sec"] = tts_res.get("duration_sec", 0)
        return result

    if event_type == "sing":
        _, body = parse_mood_delta(raw)
        reply, emotion, tts_speech, cot_hint = parse_emotion_and_clean(body)
        result["reply_text"] = reply or strip_paren_from_raw(tts_speech)
        result["emotion"] = emotion if emotion != "calm" else "gentle"
        result["stage_direction"] = extract_stage_directions(body, result["emotion"]) or "轻柔歌谣"
        lyrics_raw = _flatten_lyrics_for_tts(
            strip_paren_from_raw(tts_speech or reply or "")
        )
        if not lyrics_raw.strip():
            raise ValueError("哼唱内容生成失败，请稍后重试")
        tts_text = prepare_tts_text(
            lyrics_raw,
            result["emotion"],
            voice,
            cot_hint or SING_COT_HINT,
        )
        spd = max(0.75, speed_for_emotion(base_speed, result["emotion"]) - 0.08)
        tts_res = await _require_tts(
            text=tts_text,
            voice_type=voice,
            speed=spd,
            emotion=result["emotion"],
            context_text="缓慢轻柔的歌谣哼唱",
        )
        result["audio_url"] = tts_res["audio_url"]
        result["duration_sec"] = tts_res.get("duration_sec", 0)
        return result

    if event_type == "drowsy_snore":
        snore_marker = "[SNORE]"
        parts = raw.split(snore_marker)
        main_raw = parts[0].strip()
        _, body = parse_mood_delta(main_raw)
        reply, emotion, tts_speech, cot_hint = parse_emotion_and_clean(body)
        result["reply_text"] = reply or strip_paren_from_raw(tts_speech) or "……嗯……博士……"
        result["emotion"] = emotion if emotion != "calm" else "gentle"
        result["stage_direction"] = extract_stage_directions(body, result["emotion"]) or "困倦呢喃"
        if tts_speech.strip():
            tts_text = prepare_tts_text(
                strip_paren_from_raw(tts_speech), result["emotion"], voice, cot_hint
            )
            spd = speed_for_emotion(base_speed, result["emotion"])
            tts_res = await _try_tts(
                text=tts_text,
                voice_type=voice,
                speed=spd,
                emotion=result["emotion"],
                context_text=result["stage_direction"],
            )
            if tts_res:
                result["audio_url"] = tts_res["audio_url"]
                result["duration_sec"] = tts_res.get("duration_sec", 0)
        snore_text = "……呼……嗯……呼……"
        snore_res = await _try_tts(
            text=snore_text,
            voice_type=voice,
            speed=max(0.65, base_speed - 0.2),
            emotion="calm",
            context_text="睡梦中极轻的气声与呼噜",
        )
        if snore_res:
            result["audio_url_snore"] = snore_res["audio_url"]
        if not result["reply_text"].strip():
            raise ValueError("赠礼剧情生成失败，请稍后重试")
        return result

    raise ValueError(f"未知事件类型: {event_type}")
