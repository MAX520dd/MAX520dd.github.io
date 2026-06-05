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
    build_sing_chat_parts,
    normalize_lyrics_text,
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


def _format_gift_narrative(item: dict[str, Any], persona: dict[str, Any]) -> str:
    tpl = (item.get("gift_narrative") or "").strip()
    if not tpl:
        return (
            f"你将「{item.get('name', '礼物')}」送给了{persona.get('name', '干员')}。"
            "对方沉默片刻，似乎想说什么。"
        )
    return tpl.format(
        item_name=item.get("name", "礼物"),
        persona_name=persona.get("name", "干员"),
    )


async def _try_tts(**kwargs: Any) -> dict[str, Any] | None:
    try:
        return await tts_doubao.synthesize(**kwargs)
    except ValueError as e:
        logger.warning("gift TTS skipped: %s", e)
        return None


async def _synthesize_hum_with_retry(
    hum_raw: str,
    voice: str,
    base_speed: float,
    emotion: str,
    cot_hint: str,
    persona_id: str = "",
    retries: int = 3,
) -> dict[str, Any] | None:
    last_err: Exception | None = None
    hum_clean = normalize_lyrics_text(hum_raw, persona_id=persona_id)
    for attempt in range(max(1, retries)):
        try:
            res = await tts_doubao.synthesize_sing(
                text=hum_clean,
                voice_type=voice,
                speed=base_speed,
                emotion=emotion,
                cot_hint=cot_hint or tts_doubao.SING_LYRICS_COT_HINT,
            )
            if res.get("audio_url"):
                return res
            last_err = ValueError("TTS 未返回音频地址")
        except Exception as e:
            last_err = e
            logger.warning("gift hum TTS attempt %s failed: %s", attempt + 1, e)
    if last_err:
        logger.error("gift hum TTS all failed: %s", last_err)
    return None


def _absolute_url(path: str) -> str:
    """返回相对路径，由客户端按当前后端地址拼接。"""
    if not path:
        return ""
    if path.startswith("http"):
        from urllib.parse import urlparse

        parsed = urlparse(path)
        return parsed.path or path
    return path if path.startswith("/") else f"/{path}"


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
    narrative = _format_gift_narrative(item, persona)

    result: dict[str, Any] = {
        "event_type": event_type,
        "item_id": item_id,
        "item_name": item.get("name", ""),
        "persona_id": persona_id,
        "persona_name": persona.get("name", ""),
        "narrative_text": narrative,
        "reply_text": "",
        "lyrics_text": "",
        "stage_direction": "",
        "emotion": "calm",
        "audio_url": "",
        "audio_url_opening": "",
        "audio_url_snore": "",
        "image_url": "",
        "duration_sec": 0,
        "default_voice": voice,
        "tts_error": "",
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
        parts = build_sing_chat_parts(raw, persona_id)
        opening = parts["opening"]
        hum_clean = parts["hum_raw"]
        result["reply_text"] = opening
        result["lyrics_text"] = hum_clean
        result["emotion"] = parts["emotion"] if parts["emotion"] != "calm" else "gentle"
        result["stage_direction"] = parts["stage"]
        hum_hint = parts["hum_hint"]

        if opening.strip():
            open_tts = prepare_tts_text(
                strip_paren_from_raw(opening),
                result["emotion"],
                voice,
                "用温柔、开心、轻声的语气",
            )
            spd_o = speed_for_emotion(base_speed, result["emotion"])
            open_res = await _try_tts(
                text=open_tts,
                voice_type=voice,
                speed=spd_o,
                emotion=result["emotion"],
                context_text=emotion_context_for_tts(result["emotion"]),
            )
            if open_res:
                result["audio_url_opening"] = open_res["audio_url"]

        tts_res = await _synthesize_hum_with_retry(
            hum_clean,
            voice,
            base_speed,
            result["emotion"],
            hum_hint or tts_doubao.SING_LYRICS_COT_HINT,
            persona_id=persona_id,
        )
        if tts_res:
            result["audio_url"] = tts_res["audio_url"]
            result["duration_sec"] = tts_res.get("duration_sec", 0)
        else:
            result["tts_error"] = (
                "歌唱合成失败。请确认 DOUBAO_API_KEY、DOUBAO_CLONE_RESOURCE_ID=seed-icl-2.0、"
                "DOUBAO_TTS_MODEL=seed-tts-2.0-expressive；见 docs/doubao-tts-setup.md"
            )
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
