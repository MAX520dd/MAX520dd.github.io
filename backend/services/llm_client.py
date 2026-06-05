import asyncio
import time
from typing import Any

from openai import OpenAI

from config import settings
from services.contextual_gifts import (
    detect_scenario,
    finalize_contextual_gift,
    precheck_contextual_gift,
)
from services.easter_eggs import CRAZY_THURSDAY_SYSTEM, evaluate_crazy_thursday_offer
from services.mood import adjust_mood_delta, clamp, evaluate_red_packet_offer
from services.sticker import evaluate_sticker_offer
from services.persona import (
    build_messages,
    build_sing_chat_parts,
    emotion_context_for_tts,
    extract_stage_directions,
    get_persona,
    is_sing_request,
    parse_emotion_and_clean,
    parse_mood_delta,
    prepare_tts_text,
    resolve_mode,
    sing_friendly_mode,
    strip_paren_from_raw,
)
from services import tts_doubao


def _client() -> OpenAI:
    return OpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
    )


def _chat_sync(
    text: str,
    persona_id: str,
    history: list[dict[str, str]] | None,
    mode: str | None = None,
    doctor_state: dict[str, Any] | None = None,
    joy: int | None = None,
    affection: int | None = None,
    last_red_packet_at: float | None = None,
    last_sticker_at: float | None = None,
    last_crazy_thursday_at: float | None = None,
    last_contextual_gift_at: float | None = None,
) -> dict[str, Any]:
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置，请在 backend/.env 中填写")

    persona = get_persona(persona_id)
    if not persona:
        raise ValueError(f"未找到人物配置: {persona_id}")

    joy_before = clamp(int(joy if joy is not None else 50))
    affection_before = clamp(int(affection if affection is not None else 100))

    resolved_mode = resolve_mode(persona, text, history, mode or "auto")
    if is_sing_request(text) and persona.get("id") in ("skadi", "skadi_corrupting"):
        resolved_mode = sing_friendly_mode(persona)

    now_ts = time.time()
    easter_egg_offer = evaluate_crazy_thursday_offer(
        persona["id"],
        text,
        last_crazy_thursday_at,
        now_ts,
    )
    contextual_pre = None
    if not easter_egg_offer:
        scenario_id = detect_scenario(text)
        if scenario_id:
            contextual_pre = precheck_contextual_gift(
                persona["id"],
                scenario_id,
                affection_before,
                joy_before,
                last_contextual_gift_at,
                now_ts,
            )

    extra_parts: list[str] = []
    if easter_egg_offer:
        extra_parts.append(CRAZY_THURSDAY_SYSTEM)
    elif contextual_pre:
        extra_parts.append(contextual_pre["system_hint"])
    extra_system = "\n\n".join(extra_parts)
    messages = build_messages(
        persona, text, history, resolved_mode, doctor_state, extra_system=extra_system
    )
    client = _client()

    extra_body: dict[str, Any] = {"think": False}

    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        top_p=settings.llm_top_p,
        extra_body=extra_body,
    )

    raw = response.choices[0].message.content or ""
    raw_delta, body = parse_mood_delta(raw)
    voice = persona.get("default_voice", settings.doubao_voice_type)
    hum_text = ""
    hum_tts_text = ""
    hum_stage = ""

    sing_followup = False
    if is_sing_request(text):
        sing_followup = True
        parts = build_sing_chat_parts(raw, persona["id"])
        opening = parts["opening"]
        hum_clean = parts["hum_raw"]
        emotion = parts["emotion"] if parts["emotion"] != "cold" else "gentle"
        stage = parts["stage"]
        hum_hint = parts["hum_hint"]
        reply_text = opening
        mood_delta = adjust_mood_delta(raw_delta, emotion)
        tts_speech = strip_paren_from_raw(opening)
        tts_text = prepare_tts_text(
            tts_speech, emotion, voice, "用温柔、开心、轻声的语气"
        )
        stage_direction = stage
        tts_context = emotion_context_for_tts(emotion, "", raw)
        hum_text = hum_clean
        hum_tts_text = prepare_tts_text(
            hum_clean,
            emotion,
            voice,
            hum_hint or tts_doubao.SING_LYRICS_COT_HINT,
        )
        hum_stage = "歌唱"
    else:
        reply_text, emotion, tts_speech, cot_hint = parse_emotion_and_clean(body)
        mood_delta = adjust_mood_delta(raw_delta, emotion)
        tts_speech = strip_paren_from_raw(tts_speech)
        tts_text = prepare_tts_text(tts_speech, emotion, voice, cot_hint)
        stage_direction = extract_stage_directions(raw, emotion)
        tts_context = emotion_context_for_tts(emotion, cot_hint, raw)

    joy_after = clamp(joy_before + mood_delta)
    affection_after = clamp(affection_before + round(mood_delta * 0.6))

    contextual_gift_offer = None
    if contextual_pre:
        contextual_gift_offer = finalize_contextual_gift(
            contextual_pre, emotion, mood_delta
        )

    red_packet_offer = None
    if not easter_egg_offer and not contextual_gift_offer:
        red_packet_offer = evaluate_red_packet_offer(
            persona["id"],
            emotion,
            joy_before,
            mood_delta,
            last_red_packet_at,
            now_ts,
        )
    gift_this_turn = bool(
        easter_egg_offer or contextual_gift_offer or red_packet_offer
    )
    sticker_offer = evaluate_sticker_offer(
        persona["id"],
        emotion,
        mood_delta,
        joy_before,
        last_sticker_at,
        now_ts,
        red_packet_this_turn=gift_this_turn,
        history=history,
    )
    if easter_egg_offer and mood_delta < 3:
        mood_delta = max(mood_delta, 5)
        joy_after = clamp(joy_before + mood_delta)
    if contextual_gift_offer and mood_delta < 2:
        mood_delta = max(mood_delta, 3)
        joy_after = clamp(joy_before + mood_delta)

    return {
        "reply_text": reply_text,
        "tts_text": tts_text,
        "tts_context": tts_context,
        "stage_direction": stage_direction,
        "hum_text": hum_text,
        "hum_tts_text": hum_tts_text,
        "hum_stage": hum_stage,
        "sing_followup": sing_followup,
        "emotion": emotion,
        "mode": resolved_mode,
        "mood_delta": mood_delta,
        "joy_after": joy_after,
        "affection_after": affection_after,
        "red_packet_offer": red_packet_offer,
        "easter_egg_offer": easter_egg_offer,
        "contextual_gift_offer": contextual_gift_offer,
        "sticker_offer": sticker_offer,
        "persona_id": persona["id"],
        "persona_name": persona["name"],
        "default_voice": persona.get("default_voice", settings.doubao_voice_type),
        "default_speed": persona.get("default_speed", 1.0),
    }


async def chat(
    text: str,
    persona_id: str = "skadi",
    history: list[dict[str, str]] | None = None,
    mode: str | None = None,
    doctor_state: dict[str, Any] | None = None,
    joy: int | None = None,
    affection: int | None = None,
    last_red_packet_at: float | None = None,
    last_sticker_at: float | None = None,
    last_crazy_thursday_at: float | None = None,
    last_contextual_gift_at: float | None = None,
) -> dict[str, Any]:
    return await asyncio.to_thread(
        _chat_sync,
        text,
        persona_id,
        history,
        mode,
        doctor_state,
        joy,
        affection,
        last_red_packet_at,
        last_sticker_at,
        last_crazy_thursday_at,
        last_contextual_gift_at,
    )
