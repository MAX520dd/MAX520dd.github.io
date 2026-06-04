---
name: doubao-tts
description: >-
  豆包语音 TTS 接入知识库：V3 HTTP Chunked 单向接口、鉴权头、Resource-Id、
  cot/use_tag_parser、复刻音色、赠礼哼唱。修改 tts_doubao.py、.env TTS 变量或
  排障 InvalidModelType/401/503 时使用。
---

# 豆包语音 TTS（本项目知识库）

## 必读文档（按优先级）

1. **[docs/doubao-tts-v3-http-chunked.md](../../../docs/doubao-tts-v3-http-chunked.md)** — V3 接口选型、HTTP Chunked 请求/响应、代码映射（对应官方 [1598757 §2](https://www.volcengine.com/docs/6561/1598757?lang=zh#_2-http-chunked格式接口说明)）
2. **[docs/doubao-tts-setup.md](../../../docs/doubao-tts-setup.md)** — `.env`、cot 格式、复刻版本表、哼唱
3. **[docs/doubao-tts-401-fix.md](../../../docs/doubao-tts-401-fix.md)** — 鉴权失败

## 本项目用的接口（勿搞错）

```
POST https://openspeech.bytedance.com/api/v3/tts/unidirectional
```

**不是** WebSocket `bidirection` / `unidirectional/stream`，**不是** SSE 版。

实现：`backend/services/tts_doubao.py` → `DOUBAO_V3_URL`

## 清哼（默认）

复刻 `S_` + `<cot>嗯～哼……</cot>` → `synthesize_sing()` / `POST /v1/tts` + `hum:true`。  
禁止歌词实词；`normalize_hum_text()` 会过滤。对话与赠礼均为 **对白语音 + 清哼语音** 两条。

灿灿 `emotion=sing` 已弃用，见 [doubao-tts-sing-emotion.md](../../../docs/doubao-tts-sing-emotion.md)。

## 关键约束

| 项 | 值 |
|----|-----|
| 鉴权 | `X-Api-Key` ← `DOUBAO_API_KEY` |
| 复刻 Resource-Id | `seed-icl-2.0` + `model_type: 4`（与 `S_` 音色训练版本一致） |
| cot 表现力 | `DOUBAO_TTS_MODEL=seed-tts-2.0-expressive`，`use_tag_parser: true` |
| 文本格式 | `<cot text="情感描述">对白或歌词</cot>`，单句建议 &lt; 64 字 |
| 音频 URL | 依赖 `PUBLIC_BASE_URL` 与手机可达 IP |

## 常见改动入口

| 需求 | 文件 |
|------|------|
| 合成逻辑 / 重试 | `backend/services/tts_doubao.py` |
| 赠礼哼唱 | `backend/services/gift_events.py` + `synthesize_sing()` |
| cot 解析 | `backend/services/persona.py` → `prepare_tts_text()` |
| 环境变量 | `backend/.env`、`backend/config.py` |

## 自测

```bash
curl -s 'http://127.0.0.1:8010/health?check_tts=true'
```

官方文档索引：[162929](https://www.volcengine.com/docs/6561/162929?lang=zh)
