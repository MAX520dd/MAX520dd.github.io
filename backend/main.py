import json
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import BASE_DIR, settings
from services import asr_sensevoice, llm_client, tts_doubao
from services.tts_doubao import is_tts_auth_error
from services.doctor_state import public_meta as doctor_state_public_meta
from services.game_catalog import public_catalog
from services.gift_events import trigger_gift_event
from services.persona import get_persona, load_personas, persona_public_meta, speed_for_emotion

app = FastAPI(
    title="AI Voice Chat API",
    description="ASR + LLM + Doubao TTS 三合一网关",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """浏览器会自动请求；返回 204 避免日志里出现 404。"""
    return Response(status_code=204)


class ChatMessage(BaseModel):
    role: str
    content: str


class DoctorStatePayload(BaseModel):
    mentalState: str | None = None
    fatigue: str | None = None
    dutyStatus: str | None = None
    stress: str | None = None
    sleep: str | None = None
    injury: str | None = None
    sanity: str | None = None


class ChatRequest(BaseModel):
    text: str
    persona_id: str = "skadi"
    history: list[ChatMessage] = Field(default_factory=list)
    mode: str | None = None
    doctor_state: DoctorStatePayload | None = None
    joy: int | None = None
    affection: int | None = None
    last_red_packet_at: float | None = None


class GiftTriggerRequest(BaseModel):
    persona_id: str
    item_id: str


class TtsRequest(BaseModel):
    text: str
    voice_type: str | None = None
    speed: float = 1.0
    emotion: str = "calm"
    context_text: str | None = None


@app.get("/health")
async def health(check_tts: bool = False):
    tts_configured = settings.tts_configured
    body: dict = {
        "status": "ok",
        "asr_enabled": settings.asr_enabled,
        "llm_configured": bool(settings.llm_api_key),
        "tts_configured": tts_configured,
        "tts_auth_mode": (
            "api_key"
            if settings.doubao_tts_api_key
            else ("legacy" if settings.doubao_app_id else None)
        ),
    }
    if check_tts and tts_configured:
        probe = await tts_doubao.probe_credentials()
        body["tts_auth_ok"] = probe.get("ok", False)
        if not probe.get("ok"):
            body["tts_error"] = probe.get("error", "")
            body["tts_hint"] = probe.get("hint", "")
    return body


@app.get("/v1/personas")
async def list_personas():
    personas = load_personas()
    return {"personas": [persona_public_meta(p) for p in personas]}


@app.get("/v1/doctor-states")
async def list_doctor_states():
    return doctor_state_public_meta()


@app.get("/v1/game/catalog")
async def game_catalog():
    return public_catalog()


@app.post("/v1/gift/trigger")
async def gift_trigger(req: GiftTriggerRequest):
    persona_id = (req.persona_id or "").strip()
    item_id = (req.item_id or "").strip()
    if not persona_id or not item_id:
        raise HTTPException(status_code=400, detail="缺少 persona_id 或 item_id")
    try:
        return await trigger_gift_event(persona_id, item_id)
    except ValueError as e:
        msg = str(e)
        # TTS/上游瞬时错误：避免与「道具/干员不匹配」混为 400
        if any(
            k in msg
            for k in ("TTS", "InvalidModelType", "鉴权", "DOUBAO", "seed-icl", "合成")
        ):
            raise HTTPException(status_code=503, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/chat")
async def chat(req: ChatRequest):
    try:
        history = [h.model_dump() for h in req.history]
        ds = req.doctor_state.model_dump(exclude_none=True) if req.doctor_state else None
        result = await llm_client.chat(
            req.text,
            req.persona_id,
            history,
            req.mode,
            doctor_state=ds,
            joy=req.joy,
            affection=req.affection,
            last_red_packet_at=req.last_red_packet_at,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/tts")
async def tts(req: TtsRequest):
    try:
        result = await tts_doubao.synthesize(
            text=req.text,
            voice_type=req.voice_type,
            speed=req.speed,
            emotion=req.emotion,
            context_text=req.context_text,
        )
        return result
    except Exception as e:
        msg = str(e)
        status = 401 if is_tts_auth_error(msg) else 500
        raise HTTPException(status_code=status, detail=msg) from e


@app.post("/v1/asr")
async def asr(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        result = await asr_sensevoice.transcribe(audio_bytes, file.filename or "audio.wav")
        if not result.get("text") and result.get("error"):
            raise HTTPException(
                status_code=503,
                detail=f"ASR 不可用: {result['error']}。可传 text 字段或安装 SenseVoice 依赖。",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/v1/voice/chat")
async def voice_chat(
    file: UploadFile | None = File(None),
    text: str | None = Form(None),
    persona_id: str = Form("skadi"),
    voice_type: str | None = Form(None),
    speed: float | None = Form(None),
    mode: str | None = Form(None),
    history: str | None = Form("[]"),
    doctor_state: str | None = Form(None),
    joy: int | None = Form(None),
    affection: int | None = Form(None),
    last_red_packet_at: float | None = Form(None),
):
    """
    一键链路：音频 → ASR → LLM → TTS
    也可直接传 text 跳过 ASR。
    """
    try:
        history_list: list[dict[str, str]] = []
        if history:
            history_list = json.loads(history)

        user_text = (text or "").strip()

        if file and file.filename:
            audio_bytes = await file.read()
            asr_result = await asr_sensevoice.transcribe(audio_bytes, file.filename)
            if asr_result.get("text"):
                user_text = asr_result["text"].strip()
            elif not user_text:
                err = asr_result.get("error", "语音识别失败")
                raise HTTPException(status_code=400, detail=err)

        if not user_text:
            raise HTTPException(status_code=400, detail="请上传音频或提供 text 字段")

        ds: dict | None = None
        if doctor_state:
            ds = json.loads(doctor_state)
        chat_result = await llm_client.chat(
            user_text,
            persona_id,
            history_list,
            mode,
            doctor_state=ds,
            joy=joy,
            affection=affection,
            last_red_packet_at=last_red_packet_at,
        )

        persona = get_persona(persona_id) or {}
        voice = voice_type or chat_result.get("default_voice") or settings.doubao_voice_type
        base_speed = speed if speed is not None else chat_result.get("default_speed", 1.0)
        emotion = chat_result.get("emotion", "calm")
        final_speed = speed_for_emotion(float(base_speed), emotion)

        tts_result = await tts_doubao.synthesize(
            text=chat_result.get("tts_text") or chat_result["reply_text"],
            voice_type=voice,
            speed=final_speed,
            emotion=emotion,
            context_text=chat_result.get("tts_context")
            or chat_result.get("stage_direction"),
        )

        return {
            "user_text": user_text,
            "reply_text": chat_result["reply_text"],
            "stage_direction": chat_result.get("stage_direction", ""),
            "emotion": emotion,
            "mode": chat_result.get("mode", ""),
            "mood_delta": chat_result.get("mood_delta", 0),
            "joy_after": chat_result.get("joy_after"),
            "affection_after": chat_result.get("affection_after"),
            "red_packet_offer": chat_result.get("red_packet_offer"),
            "persona_id": chat_result.get("persona_id"),
            "persona_name": chat_result.get("persona_name"),
            "audio_url": tts_result["audio_url"],
            "duration_sec": tts_result.get("duration_sec", 0),
            "voice_type": tts_result["voice_type"],
            "speed_ratio": tts_result["speed_ratio"],
        }
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        status = 401 if is_tts_auth_error(msg) else 500
        raise HTTPException(status_code=status, detail=msg) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
