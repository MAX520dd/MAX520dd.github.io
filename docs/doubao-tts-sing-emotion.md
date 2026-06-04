# 豆包 TTS · 官方 `emotion: sing` 歌唱模式

> 参数总表：[1257584 · audio_params](https://www.volcengine.com/docs/6561/1257584?lang=zh)  
> V3 HTTP Chunked：[1598757](https://www.volcengine.com/docs/6561/1598757?lang=zh#_2-http-chunked格式接口说明)  
> SVS 产品说明：[豆包 SVS](https://www.volcengine.com/product/svs)

## 与复刻 cot 哼唱的区别

| 方式 | 音色 | 机制 | 本项目函数 |
|------|------|------|------------|
| **官方 sing** | `zh_female_cancan_mars_bigtts` 等 **2.0 大模型** | `audio_params.emotion=sing` + `enable_emotion:true` + `sing_mode` | `synthesize_official_sing()` |
| **复刻哼唱** | `S_` 复刻（斯卡蒂/浊心） | `<cot text="哼唱…">` + `seed-tts-2.0-expressive` | `synthesize_sing()` 回退路径 |

**`S_RUcfpOs32` / `S_SUcfpOs32` 传 `emotion:sing` 通常只会朗读，不会真唱。**

## 硬性条件（实测失败多卡在此）

1. **音色**：`zh_female_cancan_mars_bigtts`（灿灿）等支持 sing 的 2.0 音色  
2. **Resource-Id**：`seed-tts-2.0`（请求头 `X-Api-Resource-Id`）  
3. **模型**：`req_params.model` = `seed-tts-2.0`（不要用 `expressive` + cot 混用 sing）  
4. **必须**：`audio_params.enable_emotion: true` 且 `audio_params.emotion: "sing"`  
5. **additions**：`sing_mode: "auto"`（自动旋律）或 `manual` + `sing_score` 简谱  

## V3 请求体示例（本项目组包）

```json
{
  "user": { "uid": "ai-voice-chat" },
  "req_params": {
    "text": "小星星，亮晶晶，挂在天上放光明",
    "speaker": "zh_female_cancan_mars_bigtts",
    "model": "seed-tts-2.0",
    "audio_params": {
      "format": "mp3",
      "sample_rate": 24000,
      "emotion": "sing",
      "enable_emotion": true,
      "emotion_scale": 4
    },
    "additions": "{\"sing_mode\":\"auto\",\"bpm\":95}"
  }
}
```

```http
POST https://openspeech.bytedance.com/api/v3/tts/unidirectional
X-Api-Key: <DOUBAO_API_KEY>
X-Api-Resource-Id: seed-tts-2.0
X-Api-Request-Id: <uuid>
```

HTTP / 单向 WS / 双向 WS 参数结构一致，本项目当前仅实现 **HTTP Chunked**。

## 本项目配置（`backend/.env`）

```env
DOUBAO_SING_ENABLED=true
DOUBAO_SING_VOICE=zh_female_cancan_mars_bigtts
DOUBAO_SING_RESOURCE_ID=seed-tts-2.0
DOUBAO_SING_MODE=auto
DOUBAO_SING_BPM=95
DOUBAO_SING_EMOTION_SCALE=4
```

开启后，赠礼 `event_type: sing` 会**先**走 `synthesize_official_sing()`，失败再回退浊心复刻 cot 哼唱。

## 1 分钟自测

```bash
cd backend && source .venv/bin/activate
python ../scripts/test-doubao-sing.py
```

成功时输出 `backend/static/audio/sing-*.mp3` 文件大小 &gt; 0（实测约 39KB+），听感应为**唱歌**而非念白。

若 `seed-tts-2.0` 报 Resource-Id 与 speaker 不匹配，代码会自动依次尝试 `seed-tts-1.0` 等（见 `synthesize_official_sing`）。

## 本项目此前为何「不能 sing」

- 默认音色是 **复刻 `S_SUcfpOs32`**，只走了 **cot 哼唱**，未传 `audio_params.emotion=sing`。
- `[emotion:sing]` 人设标签 **不会** 自动映射到火山 API。
- 现已增加 `synthesize_official_sing()`；赠礼在 `DOUBAO_SING_ENABLED=true` 时优先真唱，失败再回退浊心复刻 cot。

## 为何不用 `[emotion:sing]` 标签

LLM 的 `[emotion:xxx]` 是本项目人设标记；火山只认请求体里的 `audio_params.emotion`。二者需在代码里映射，见 `persona.VALID_EMOTIONS` 与 `synthesize_official_sing()`。
