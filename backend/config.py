import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_api_key: str = ""
    # 与官方文档一致，可与 LLM_API_KEY 二选一（export ARK_API_KEY=ark-xxx）
    ark_api_key: str = ""
    llm_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    # 火山方舟推理接入点 ID，形如 ep-xxxxxxxxxx-xxxxx
    llm_model: str = "ep-xxxxxxxxxx-xxxxx"
    llm_temperature: float = 0.9
    llm_max_tokens: int = 256
    llm_top_p: float = 0.9

    # 新版控制台：API Key 管理 → 复制 Key（推荐，对应请求头 X-Api-Key）
    doubao_api_key: str = ""
    # 已废弃：旧版应用管理 AppID，仅在与下方 Token 成对时作鉴权回退
    doubao_app_id: str = ""
    # 兼容旧变量名；与 DOUBAO_API_KEY 等价
    doubao_access_token: str = ""
    doubao_voice_type: str = "S_SUcfpOs32"
    doubao_resource_id: str = "seed-tts-2.0"
    # 声音复刻音色（voice_type 以 S_ 开头）使用的 V3 资源 ID
    doubao_clone_resource_id: str = "seed-icl-2.0"
    # 单向 HTTP：声音复刻 2.0 表现力版 + cot 标签解析（见 docs/doubao-tts-setup.md）
    doubao_use_tag_parser: bool = True
    doubao_tts_model: str = "seed-tts-2.0-expressive"
    doubao_cluster: str = "volcano_tts"
    doubao_cluster_icl: str = "volcano_icl"
    # 官方 SVS/歌手音色 sing（仅 2.0 大模型音色如灿灿，复刻 S_ 无效）
    doubao_sing_enabled: bool = False
    doubao_sing_voice: str = "zh_female_cancan_mars_bigtts"
    doubao_sing_resource_id: str = "seed-tts-2.0"
    doubao_sing_mode: str = "auto"
    doubao_sing_bpm: int = 95
    doubao_sing_emotion_scale: float = 4.0

    asr_enabled: bool = True
    asr_model: str = "iic/SenseVoiceSmall"

    host: str = "0.0.0.0"
    port: int = 8000
    public_base_url: str = "http://127.0.0.1:8000"

    @model_validator(mode="after")
    def _merge_env_aliases(self) -> "Settings":
        if not self.llm_api_key:
            self.llm_api_key = self.ark_api_key or os.environ.get("ARK_API_KEY", "")
        env_tts_key = os.environ.get("DOUBAO_API_KEY", "")
        if not self.doubao_api_key:
            self.doubao_api_key = (
                self.doubao_access_token or env_tts_key
            )
        if not self.doubao_access_token:
            self.doubao_access_token = self.doubao_api_key or env_tts_key
        return self

    @property
    def doubao_tts_api_key(self) -> str:
        """豆包语音 V3 鉴权密钥（新版 X-Api-Key）。"""
        return self.doubao_api_key or self.doubao_access_token

    @property
    def tts_configured(self) -> bool:
        return bool(self.doubao_tts_api_key)

    @property
    def ark_chat_url(self) -> str:
        """方舟在线推理 Chat Completions 完整地址。"""
        return f"{self.llm_base_url.rstrip('/')}/chat/completions"

    @property
    def audio_dir(self) -> Path:
        d = BASE_DIR / "static" / "audio"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def personas_path(self) -> Path:
        return BASE_DIR / "data" / "personas.json"


settings = Settings()
