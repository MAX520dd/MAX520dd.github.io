import io
import tempfile
from pathlib import Path
from typing import Any

from config import settings

_model = None
_model_load_error: str | None = None


def _load_model():
    global _model, _model_load_error
    if _model is not None:
        return _model
    if _model_load_error:
        raise RuntimeError(_model_load_error)
    try:
        from funasr import AutoModel

        _model = AutoModel(
            model=settings.asr_model,
            trust_remote_code=True,
            disable_update=True,
        )
        return _model
    except Exception as e:
        _model_load_error = str(e)
        raise


def _to_wav_16k(audio_bytes: bytes, suffix: str) -> Path:
    """将上传音频转为 16k mono wav 临时文件。"""
    import soundfile as sf
    import numpy as np

    tmp_in = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_in.write(audio_bytes)
    tmp_in.close()

    data, sr = sf.read(tmp_in.name, dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=1)

    if sr != 16000:
        try:
            import torchaudio
            import torch

            t = torch.from_numpy(data).unsqueeze(0)
            resampler = torchaudio.transforms.Resample(sr, 16000)
            t = resampler(t)
            data = t.squeeze(0).numpy()
            sr = 16000
        except Exception:
            # 简单线性重采样兜底
            duration = len(data) / sr
            new_len = int(duration * 16000)
            indices = np.linspace(0, len(data) - 1, new_len)
            data = np.interp(indices, np.arange(len(data)), data).astype(np.float32)
            sr = 16000

    tmp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp_out.name, data, sr)
    return Path(tmp_out.name)


async def transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> dict[str, Any]:
    if not settings.asr_enabled:
        return {
            "text": "[ASR 已关闭] 请在请求中使用 text 字段，或设置 ASR_ENABLED=true",
            "lang": "zh",
            "mock": True,
        }

    suffix = Path(filename).suffix or ".wav"
    wav_path = _to_wav_16k(audio_bytes, suffix)

    try:
        model = _load_model()
        result = model.generate(
            input=str(wav_path),
            cache={},
            language="auto",
            use_itn=True,
        )
        text = ""
        if result and len(result) > 0:
            item = result[0]
            if isinstance(item, dict):
                text = item.get("text", "") or item.get("value", "")
            else:
                text = str(item)
        text = text.strip()
        return {"text": text, "lang": "zh", "mock": False}
    except Exception as e:
        # 开发环境降级：便于无模型时联调其它链路
        return {
            "text": "",
            "lang": "zh",
            "mock": True,
            "error": str(e),
        }
    finally:
        try:
            wav_path.unlink(missing_ok=True)
        except OSError:
            pass
