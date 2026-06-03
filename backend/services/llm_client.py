import asyncio
import time
from typing import Any

from openai import OpenAI

from config import settings
from services.mood import adjust_mood_delta, clamp, evaluate_red_packet_offer
from services.persona import (
    build_messages,
    emotion_context_for_tts,
    extract_stage_directions,
    get_persona,
    parse_emotion_and_clean,
    parse_mood_delta,
    prepare_tts_text,
    resolve_mode,
    strip_paren_from_raw,
)


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
) -> dict[str, Any]:
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY 未配置，请在 backend/.env 中填写")

    persona = get_persona(persona_id)
    if not persona:
        raise ValueError(f"未找到人物配置: {persona_id}")

    resolved_mode = resolve_mode(persona, text, history, mode or "auto")
    messages = build_messages(persona, text, history, resolved_mode, doctor_state)
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
    reply_text, emotion, tts_speech, cot_hint = parse_emotion_and_clean(body)
    mood_delta = adjust_mood_delta(raw_delta, emotion)
    tts_speech = strip_paren_from_raw(tts_speech)
    voice = persona.get("default_voice", settings.doubao_voice_type)
    tts_text = prepare_tts_text(tts_speech, emotion, voice, cot_hint)
    stage_direction = extract_stage_directions(raw, emotion)
    tts_context = emotion_context_for_tts(emotion, cot_hint, raw)

    joy_before = clamp(int(joy if joy is not None else 50))
    joy_after = clamp(joy_before + mood_delta)
    affection_before = clamp(int(affection if affection is not None else 100))
    affection_after = clamp(affection_before + round(mood_delta * 0.6))

    red_packet_offer = evaluate_red_packet_offer(
        persona["id"],
        emotion,
        joy_before,
        mood_delta,
        last_red_packet_at,
        time.time(),
    )

    return {
        "reply_text": reply_text,
        "tts_text": tts_text,
        "tts_context": tts_context,
        "stage_direction": stage_direction,
        "emotion": emotion,
        "mode": resolved_mode,
        "mood_delta": mood_delta,
        "joy_after": joy_after,
        "affection_after": affection_after,
        "red_packet_offer": red_packet_offer,
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
    )
