import base64
import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

from config import settings
from services.persona import (
    emotion_context_for_tts,
    strip_display_markup,
    speed_for_emotion,
)

logger = logging.getLogger(__name__)

DOUBAO_V3_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
DOUBAO_V1_URL = "https://openspeech.bytedance.com/api/v1/tts"

# 声音复刻 S_ 音色：Resource-Id 与 additions.model_type 必须成对（见火山文档）
CLONE_RESOURCE_CONFIGS: tuple[tuple[str, int], ...] = (
    ("seed-icl-2.0", 4),
    ("seed-icl-1.0-concurr", 3),
    ("seed-icl-1.0", 1),
)

_RESOURCE_TO_MODEL_TYPE = {rid: mt for rid, mt in CLONE_RESOURCE_CONFIGS}

# 情绪 -> 豆包 context_texts（自然语言情感，仅首条生效）
# 赠礼哼唱：豆包单向 HTTP + seed-tts-2.0-expressive + use_tag_parser（见 docs/doubao-tts-setup.md）
SING_LYRICS_COT_HINT = (
    "用轻柔、带旋律感的歌声吟唱，歌词吐字清晰、节奏舒缓，"
    "句与句之间自然停顿，像潮声轻拍海岸"
)

# 兼容旧名
SING_COT_HINT = SING_LYRICS_COT_HINT

EMOTION_CONTEXT_TEXTS: dict[str, str] = {
    "happy": "用轻快、略带笑意的语气",
    "calm": "用平静、沉静的语气",
    "sad": "用低沉、略带哀伤的语气",
    "melancholy": "用忧郁、克制的语气",
    "possessive": "用低沉、占有欲强的语气",
    "cold": "用冷淡、疏离的语气",
    "gentle": "用温柔、轻声的语气",
}


def _estimate_duration_sec(text: str) -> int:
    return max(1, min(60, len(text) // 4 + 1))


def _tts_api_key() -> str:
    return settings.doubao_tts_api_key


def _auth_header_bearer() -> str:
    return f"Bearer;{_tts_api_key()}"


def _is_clone_voice(voice_type: str) -> bool:
    return voice_type.startswith("S_")


def _clone_configs_to_try() -> list[tuple[str, int]]:
    """返回 (resource_id, model_type) 列表，优先 .env 配置。

    已在 .env 指定 DOUBAO_CLONE_RESOURCE_ID 时仅尝试该版本，避免 ICL2.0 音色
    回退到 seed-icl-1.0 触发 InvalidModelType 并掩盖真实错误。
    """
    custom = (settings.doubao_clone_resource_id or "").strip()
    if custom:
        mt = _RESOURCE_TO_MODEL_TYPE.get(custom, 4 if custom == "seed-icl-2.0" else 1)
        return [(custom, mt)]
    return list(CLONE_RESOURCE_CONFIGS)


def _build_additions(
    model_type: int,
    context_text: str = "",
    *,
    use_tag_parser: bool = False,
) -> str:
    """additions 为 JSON 字符串。tag_parser 时开启 cot 解析，否则用 context_texts。"""
    extra: dict[str, Any] = {"model_type": model_type}
    if use_tag_parser:
        extra["use_tag_parser"] = True
    elif context_text:
        extra["context_texts"] = [context_text]
    return json.dumps(extra, ensure_ascii=False)


def _build_v3_clone_payload(
    text: str,
    speaker_id: str,
    speed_ratio: float,
    model_type: int,
    context_text: str = "",
    *,
    use_tag_parser: bool = False,
) -> dict[str, Any]:
    """V3 声音复刻：speaker 填 S_ 开头。"""
    speech_rate = int((speed_ratio - 1.0) * 100)
    req_params: dict[str, Any] = {
        "text": text,
        "speaker": speaker_id,
        "audio_params": {
            "format": "mp3",
            "sample_rate": 24000,
            "speech_rate": speech_rate,
        },
        "additions": _build_additions(
            model_type, context_text, use_tag_parser=use_tag_parser
        ),
    }
    model = settings.doubao_tts_model
    if use_tag_parser and model:
        req_params["model"] = model
    return {"user": {"uid": "ai-voice-chat"}, "req_params": req_params}


def _apply_expressive_model(payload: dict[str, Any], force: bool) -> dict[str, Any]:
    """哼唱等场景强制 seed-tts-2.0-expressive。"""
    if not force:
        return payload
    rp = payload.setdefault("req_params", {})
    if settings.doubao_use_tag_parser:
        rp["model"] = settings.doubao_tts_model or "seed-tts-2.0-expressive"
    return payload


# 官方歌手合成：audio_params.emotion=sing（仅部分 2.0 音色，如灿灿）
# 文档：https://www.volcengine.com/docs/6561/1257584 · V3：https://www.volcengine.com/docs/6561/1598757
OFFICIAL_SING_VOICE_DEFAULT = "zh_female_cancan_mars_bigtts"


def _build_v3_official_sing_payload(
    text: str,
    speaker: str,
    *,
    sing_mode: str = "auto",
    bpm: int = 95,
    emotion_scale: float = 4.0,
    sing_score: str = "",
) -> dict[str, Any]:
    """V3 大模型 2.0 + enable_emotion + emotion=sing + sing_mode（非复刻 S_ 音色）。"""
    plain = strip_display_markup(text).strip()
    if not plain:
        raise ValueError("歌唱文本为空")
    additions: dict[str, Any] = {"sing_mode": sing_mode, "bpm": bpm}
    if sing_mode == "manual" and sing_score.strip():
        additions["sing_score"] = sing_score.strip()
    scale = max(1.0, min(5.0, float(emotion_scale)))
    req_params: dict[str, Any] = {
        "text": plain,
        "speaker": speaker,
        "model": settings.doubao_sing_resource_id or "seed-tts-2.0",
        "audio_params": {
            "format": "mp3",
            "sample_rate": 24000,
            "emotion": "sing",
            "enable_emotion": True,
            "emotion_scale": scale,
        },
        "additions": json.dumps(additions, ensure_ascii=False),
    }
    return {"user": {"uid": "ai-voice-chat"}, "req_params": req_params}


def _build_v3_standard_payload(
    text: str,
    speaker: str,
    speed_ratio: float,
    context_text: str = "",
) -> dict[str, Any]:
    """V3 大模型音色：speaker 为控制台音色 ID（如 zh_female_*_bigtts）。"""
    speech_rate = int((speed_ratio - 1.0) * 100)
    req_params: dict[str, Any] = {
        "text": text,
        "speaker": speaker,
        "audio_params": {
            "format": "mp3",
            "sample_rate": 24000,
            "speech_rate": speech_rate,
        },
    }
    if context_text:
        req_params["additions"] = json.dumps(
            {"context_texts": [context_text]}, ensure_ascii=False
        )
    return {"user": {"uid": "ai-voice-chat"}, "req_params": req_params}


def _standard_resource_ids_to_try() -> list[str]:
    custom = settings.doubao_resource_id
    ids: list[str] = []
    if custom:
        ids.append(custom)
    for rid in ("seed-tts-2.0", "seed-tts-1.0-concurr", "seed-tts-1.0"):
        if rid not in ids:
            ids.append(rid)
    return ids


def _build_v1_payload(
    text: str,
    voice_type: str,
    speed_ratio: float,
    reqid: str,
) -> dict[str, Any]:
    cluster = settings.doubao_cluster_icl if _is_clone_voice(voice_type) else settings.doubao_cluster
    return {
        "app": {
            "appid": settings.doubao_app_id,
            "token": settings.doubao_access_token,
            "cluster": cluster,
        },
        "user": {"uid": "ai-voice-chat"},
        "audio": {
            "voice_type": voice_type,
            "encoding": "mp3",
            "speed_ratio": speed_ratio,
        },
        "request": {
            "reqid": reqid,
            "text": text,
            "operation": "query",
        },
    }


def _extract_audio_bytes(data: dict[str, Any]) -> bytes:
    if "data" in data and isinstance(data["data"], str):
        return base64.b64decode(data["data"])
    if "audio" in data and isinstance(data["audio"], str):
        return base64.b64decode(data["audio"])
    if "payload" in data:
        payload = data["payload"]
        if isinstance(payload, str):
            return base64.b64decode(payload)
        if isinstance(payload, dict):
            if "audio" in payload and isinstance(payload["audio"], str):
                return base64.b64decode(payload["audio"])
            if "data" in payload and isinstance(payload["data"], str):
                return base64.b64decode(payload["data"])
    raise ValueError(f"无法解析 TTS 响应: {json.dumps(data, ensure_ascii=False)[:500]}")


def _parse_error_body(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        header = body.get("header")
        if isinstance(header, dict):
            msg = header.get("message")
            if msg:
                code = header.get("code")
                return f"{msg} (code={code})" if code is not None else str(msg)
        return body.get("message") or body.get("msg") or body.get("error") or str(body)
    except Exception:
        return resp.text[:300]


def is_tts_auth_error(msg: str) -> bool:
    low = msg.lower()
    return any(
        k in low
        for k in (
            "鉴权",
            "401",
            "grant",
            "authenticate",
            "app key not found",
            "45000010",
            "45000000",
            "load grant",
        )
    )


def _friendly_error(msg: str, resource_id: str = "") -> str:
    low = msg.lower()
    if "resource id is mismatched" in low or "mismatched with speaker" in low:
        return (
            f"音色与 Resource-Id 不匹配：{msg}。"
            f"请在 .env 设置 DOUBAO_CLONE_RESOURCE_ID（当前尝试 {resource_id or 'seed-icl-1.0/2.0'}），"
            "须与控制台该音色训练版本一致（ICL1.0→seed-icl-1.0，ICL2.0→seed-icl-2.0）。"
        )
    if (
        "401" in low
        or "authenticate" in low
        or "grant" in low
        or "app key not found" in low
        or "45000010" in msg
        or "45000000" in msg
    ):
        return (
            f"TTS 鉴权失败：{msg}。请在 backend/.env 填写 "
            "DOUBAO_API_KEY（控制台 → API Key 管理）。"
            "若仍使用旧版应用，可额外保留 DOUBAO_APP_ID 与 DOUBAO_ACCESS_TOKEN 作回退。"
        )
    return msg


def _parse_v3_ndjson_body(raw: str, resource_id: str) -> bytes:
    """V3 单向流式接口返回 NDJSON，逐行拼接 base64 音频。"""
    chunks: list[bytes] = []
    last_err = ""
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        code = data.get("code")
        payload = data.get("data")
        if code in (0, 3000) and payload:
            chunks.append(base64.b64decode(payload))
            continue
        if code == 20000000:
            break
        if code not in (0, None, 3000):
            last_err = data.get("message") or str(data)
    if chunks:
        return b"".join(chunks)
    if last_err:
        raise ValueError(_friendly_error(last_err, resource_id))
    # 少数账号仍返回单条 JSON
    try:
        data = json.loads(raw)
        return _extract_audio_bytes(data)
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(
            _friendly_error(last_err or f"无法解析 TTS 响应: {raw[:300]}", resource_id)
        ) from e


def _v3_header_variants(resource_id: str, reqid: str) -> list[dict[str, str]]:
    """
    V3 鉴权：优先新版 X-Api-Key；旧版控制台回退 X-Api-App-Id + X-Api-Access-Key。
    见 https://www.volcengine.com/docs/6561/1598757
    """
    base = {
        "Content-Type": "application/json",
        "X-Api-Resource-Id": resource_id,
        "X-Api-Request-Id": reqid,
    }
    variants: list[dict[str, str]] = []
    api_key = _tts_api_key()
    if api_key:
        variants.append({**base, "X-Api-Key": api_key})
    app_id = settings.doubao_app_id
    legacy_token = settings.doubao_access_token or api_key
    if app_id and legacy_token:
        legacy_base = {**base, "X-Api-Access-Key": legacy_token}
        variants.append({**legacy_base, "X-Api-App-Id": app_id})
        variants.append({**legacy_base, "X-Api-App-Key": app_id})
    seen: set[tuple[tuple[str, str], ...]] = set()
    unique: list[dict[str, str]] = []
    for h in variants:
        sig = tuple(sorted(h.items()))
        if sig not in seen:
            seen.add(sig)
            unique.append(h)
    return unique


async def _post_v3_tts(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> tuple[bytes, str]:
    resource_id = headers.get("X-Api-Resource-Id", "")
    resp = await client.post(DOUBAO_V3_URL, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise ValueError(_friendly_error(_parse_error_body(resp), resource_id))
    return _parse_v3_ndjson_body(resp.text, resource_id), resource_id


async def _post_json(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> tuple[bytes, str]:
    resp = await client.post(url, headers=headers, json=payload)
    rid = headers.get("X-Api-Resource-Id", "")
    if resp.status_code >= 400:
        raise ValueError(_friendly_error(_parse_error_body(resp), rid))
    data = resp.json()
    code = data.get("code")
    if code not in (0, None, 3000) and "data" not in data and "audio" not in data:
        msg = data.get("message") or str(data)
        raise ValueError(_friendly_error(msg, rid))
    return _extract_audio_bytes(data), rid


async def synthesize_official_sing(
    text: str,
    voice_type: str | None = None,
    save_filename: str | None = None,
    *,
    sing_mode: str | None = None,
    bpm: int | None = None,
    emotion_scale: float | None = None,
) -> dict[str, Any]:
    """
    火山官方 emotion=sing（歌手音色 / SVS 规则）。
    硬性要求：2.0 大模型音色（默认灿灿）、Resource-Id=seed-tts-2.0、enable_emotion=true。
    复刻音色 S_ 传 sing 只会朗读，见 docs/doubao-tts-sing-emotion.md。
    """
    if not settings.tts_configured:
        raise ValueError("豆包 TTS 未配置 DOUBAO_API_KEY")

    voice = (voice_type or settings.doubao_sing_voice or OFFICIAL_SING_VOICE_DEFAULT).strip()
    if _is_clone_voice(voice):
        raise ValueError(
            f"emotion=sing 不支持复刻音色 {voice}，请改用 zh_female_cancan_mars_bigtts 等 2.0 歌手音色"
        )

    reqid = str(uuid.uuid4())
    resource_id = (settings.doubao_sing_resource_id or "seed-tts-2.0").strip()
    payload = _build_v3_official_sing_payload(
        text,
        voice,
        sing_mode=sing_mode or settings.doubao_sing_mode or "auto",
        bpm=bpm if bpm is not None else settings.doubao_sing_bpm,
        emotion_scale=emotion_scale
        if emotion_scale is not None
        else settings.doubao_sing_emotion_scale,
    )

    audio_bytes: bytes | None = None
    used_rid = ""
    errors: list[str] = []
    resource_ids = [resource_id]
    for rid in _standard_resource_ids_to_try():
        if rid not in resource_ids:
            resource_ids.append(rid)

    async with httpx.AsyncClient(timeout=90.0) as client:
        for rid in resource_ids:
            payload["req_params"]["model"] = rid
            for headers in _v3_header_variants(rid, reqid):
                try:
                    audio_bytes, used_rid = await _post_v3_tts(client, headers, payload)
                    break
                except Exception as e:
                    errors.append(f"[{rid}] {e}")
            if audio_bytes:
                resource_id = used_rid
                break

    if audio_bytes is None:
        raise ValueError(errors[-1] if errors else "官方 sing 合成失败")

    filename = save_filename or f"sing-{reqid}.mp3"
    out_path: Path = settings.audio_dir / filename
    out_path.write_bytes(audio_bytes)
    audio_url = f"/static/audio/{filename}"
    plain = strip_display_markup(text)
    return {
        "audio_url": audio_url,
        "audio_path": str(out_path),
        "filename": filename,
        "voice_type": voice,
        "resource_id": resource_id,
        "speed_ratio": 1.0,
        "emotion": "sing",
        "duration_sec": _estimate_duration_sec(plain),
        "sing_mode": "official_emotion_sing",
    }


async def synthesize_sing(
    text: str,
    voice_type: str | None = None,
    speed: float = 1.0,
    emotion: str = "gentle",
    cot_hint: str | None = None,
    save_filename: str | None = None,
) -> dict[str, Any]:
    """
    复刻音色歌唱：表现力版 + <cot>歌词</cot>（不用灿灿 emotion=sing）。
    """
    from services.persona import (
        normalize_lyrics_text,
        prepare_tts_text,
        speed_for_emotion,
        strip_paren_from_raw,
    )

    voice = voice_type or settings.doubao_voice_type
    hint = (cot_hint or "").strip() or SING_LYRICS_COT_HINT
    raw = normalize_lyrics_text(strip_paren_from_raw(text))
    if not raw.strip():
        raise ValueError("歌词内容为空")
    tts_text = prepare_tts_text(raw, emotion, voice, hint)
    plain = strip_display_markup(tts_text)
    if len(plain) > 96:
        plain = plain[:92] + "……"
        tts_text = prepare_tts_text(plain, emotion, voice, hint)
    spd = max(0.72, speed_for_emotion(speed, emotion) - 0.12)
    return await synthesize(
        text=tts_text,
        voice_type=voice,
        speed=spd,
        emotion=emotion,
        context_text="",
        save_filename=save_filename,
        force_expressive=True,
    )


async def synthesize(
    text: str,
    voice_type: str | None = None,
    speed: float = 1.0,
    emotion: str = "calm",
    context_text: str | None = None,
    save_filename: str | None = None,
    *,
    force_expressive: bool = False,
) -> dict[str, Any]:
    if not settings.tts_configured:
        raise ValueError(
            "豆包 TTS 未配置，请在 backend/.env 填写 DOUBAO_API_KEY"
            "（火山语音控制台 → API Key 管理）"
        )

    voice = voice_type or settings.doubao_voice_type
    use_tag_parser = settings.doubao_use_tag_parser and _is_clone_voice(voice)
    if use_tag_parser:
        ctx = ""
    else:
        text = strip_display_markup(text)
        ctx = (context_text or "").strip() or emotion_context_for_tts(emotion)
    speed_ratio = speed_for_emotion(speed, emotion)
    reqid = str(uuid.uuid4())

    audio_bytes: bytes | None = None
    used_resource_id = ""
    errors: list[str] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        if _is_clone_voice(voice):
            # 声音复刻：V3 + Resource-Id + additions.model_type 成对
            for resource_id, model_type in _clone_configs_to_try():
                payload = _build_v3_clone_payload(
                    text,
                    voice,
                    speed_ratio,
                    model_type,
                    ctx,
                    use_tag_parser=use_tag_parser,
                )
                payload = _apply_expressive_model(payload, force_expressive)
                for headers in _v3_header_variants(resource_id, reqid):
                    try:
                        audio_bytes, used_resource_id = await _post_v3_tts(
                            client, headers, payload
                        )
                        break
                    except Exception as e:
                        errors.append(f"[{resource_id}/mt{model_type}] {e}")
                if audio_bytes:
                    break
        else:
            # 大模型音色：V3（新版 API Key）；旧账号可回退 V1
            for resource_id in _standard_resource_ids_to_try():
                payload = _build_v3_standard_payload(
                    text, voice, speed_ratio, ctx
                )
                for headers in _v3_header_variants(resource_id, reqid):
                    try:
                        audio_bytes, used_resource_id = await _post_v3_tts(
                            client, headers, payload
                        )
                        break
                    except Exception as e:
                        errors.append(f"[v3/{resource_id}] {e}")
                if audio_bytes:
                    break
            if audio_bytes is None and settings.doubao_app_id:
                try:
                    audio_bytes, used_resource_id = await _post_json(
                        client,
                        DOUBAO_V1_URL,
                        {
                            "Authorization": _auth_header_bearer(),
                            "Content-Type": "application/json",
                        },
                        _build_v1_payload(text, voice, speed_ratio, reqid),
                    )
                except Exception as e:
                    errors.append(f"[v1] {e}")

    if audio_bytes is None:
        preferred = (settings.doubao_clone_resource_id or "").strip()
        err = errors[-1] if errors else "TTS 合成失败"
        if preferred:
            for line in errors:
                if preferred in line:
                    err = line
                    break
        raise ValueError(err)

    filename = save_filename or f"{reqid}.mp3"
    out_path: Path = settings.audio_dir / filename
    out_path.write_bytes(audio_bytes)

    audio_url = f"/static/audio/{filename}"

    return {
        "audio_url": audio_url,
        "audio_path": str(out_path),
        "filename": filename,
        "voice_type": voice,
        "resource_id": used_resource_id,
        "speed_ratio": speed_ratio,
        "emotion": emotion,
        "duration_sec": _estimate_duration_sec(text),
    }


_tts_probe_cache: dict[str, Any] | None = None
_tts_probe_at: float = 0.0
_TTS_PROBE_TTL_SEC = 90.0


async def probe_credentials(force: bool = False) -> dict[str, Any]:
    """
    向豆包发起一次最小合成请求，验证 API Key（或旧版 AppID+Token）是否有效。
    结果缓存约 90 秒，避免频繁打外部 API。
    """
    global _tts_probe_cache, _tts_probe_at

    if not settings.tts_configured:
        return {
            "ok": False,
            "error": "未配置 DOUBAO_API_KEY",
            "hint": (
                "打开 https://console.volcengine.com/speech → API Key 管理 → "
                "创建/复制 API Key，写入 backend/.env 的 DOUBAO_API_KEY 后重启后端。"
            ),
        }

    now = time.time()
    if (
        not force
        and _tts_probe_cache is not None
        and now - _tts_probe_at < _TTS_PROBE_TTL_SEC
    ):
        return _tts_probe_cache

    voice = settings.doubao_voice_type
    resource_id, model_type = _clone_configs_to_try()[0]
    use_tp = settings.doubao_use_tag_parser and _is_clone_voice(voice)
    probe_text = '<cot text="平静的语气">测</cot>' if use_tp else "测"
    ctx = "" if use_tp else emotion_context_for_tts("calm")
    payload = _build_v3_clone_payload(
        probe_text,
        voice,
        1.0,
        model_type,
        ctx,
        use_tag_parser=use_tp,
    )
    reqid = str(uuid.uuid4())
    result: dict[str, Any]

    auth_mode = "api_key" if _tts_api_key() else "legacy"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            last_err: Exception | None = None
            for headers in _v3_header_variants(resource_id, reqid):
                try:
                    await _post_v3_tts(client, headers, payload)
                    last_err = None
                    break
                except Exception as e:
                    last_err = e
            if last_err is not None:
                raise last_err
        result = {
            "ok": True,
            "auth_mode": auth_mode,
            "voice_type": voice,
            "resource_id": resource_id,
        }
    except Exception as e:
        msg = str(e)
        result = {
            "ok": False,
            "auth_mode": auth_mode,
            "error": msg,
            "hint": (
                "打开 https://console.volcengine.com/speech → API Key 管理 → "
                "复制 API Key 到 backend/.env 的 DOUBAO_API_KEY，保存后重启后端。"
            ),
            "auth_error": is_tts_auth_error(msg),
        }

    _tts_probe_cache = result
    _tts_probe_at = now
    return result
