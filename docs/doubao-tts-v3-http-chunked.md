# 豆包语音 V3 · HTTP Chunked 单向流式接口（知识库）

> 官方原文：[1598757 · 单向流式 http V3](https://www.volcengine.com/docs/6561/1598757?lang=zh)  
> HTTP Chunked 章节锚点：[§2 HTTP Chunked 格式接口说明](https://www.volcengine.com/docs/6561/1598757?lang=zh#_2-http-chunked格式接口说明)  
> 本项目实现：`backend/services/tts_doubao.py` → `DOUBAO_V3_URL`

---

## 1. 四种 V3 接口对照（选哪个）

| 接口地址 | 协议 | 推荐场景 | 本项目 |
|----------|------|----------|--------|
| `wss://openspeech.bytedance.com/api/v3/tts/bidirection` | WebSocket 双向 | 实时交互、流式输入+流式输出 | **未使用** |
| `wss://openspeech.bytedance.com/api/v3/tts/unidirectional/stream` | WebSocket 单向 | 一次性文本、流式音频 | **未使用** |
| **`https://openspeech.bytedance.com/api/v3/tts/unidirectional`** | **HTTP Chunked** | **一次性提交全文、流式返回音频** | **✅ 当前接入** |
| `https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse` | HTTP SSE | 一次性文本、SSE 流式音频 | **未使用** |

能力上均支持：语音合成、声音复刻、混音。本仓库对话 / 赠礼 / 哼唱均走 **第三行 HTTP Chunked**。

---

## 2. HTTP Chunked 接口要点（官方 §2 摘要）

### 2.1 基本信息

| 项 | 值 |
|----|-----|
| 方法 | `POST` |
| URL | `https://openspeech.bytedance.com/api/v3/tts/unidirectional` |
| Content-Type | `application/json` |
| 传输 | 响应体为 **Chunked / 按行 NDJSON** 流式返回音频分片 |

### 2.2 请求头（Header）

| Header | 必填 | 说明 |
|--------|------|------|
| `X-Api-Key` | 新版推荐 | 控制台 [API Key 管理](https://console.volcengine.com/speech) |
| `X-Api-Resource-Id` | 是 | 与音色类型匹配，见下文 Resource-Id 表 |
| `X-Api-Request-Id` | 建议 | 单次请求 UUID，便于排障 |
| `X-Api-App-Id` + `X-Api-Access-Key` | 旧版回退 | 应用管理废弃后仅部分账号可用 |

本项目 `_v3_header_variants()` 会依次尝试 `X-Api-Key`，再回退 AppId+Token。

### 2.3 请求体（Body）结构

```json
{
  "user": {
    "uid": "ai-voice-chat"
  },
  "req_params": {
    "text": "<cot text=\"温柔的语气\">博士，我在这里。</cot>",
    "speaker": "S_SUcfpOs32",
    "model": "seed-tts-2.0-expressive",
    "audio_params": {
      "format": "mp3",
      "sample_rate": 24000,
      "speech_rate": 0
    },
    "additions": "{\"model_type\":4,\"use_tag_parser\":true}"
  }
}
```

| 字段 | 说明 |
|------|------|
| `req_params.text` | 待合成文本；复刻 2.0 表现力版可写 `<cot text=\"…\">对白</cot>` |
| `req_params.speaker` | 音色 ID：复刻 `S_` 开头；大模型音色为控制台 ID |
| `req_params.model` | 如 `seed-tts-2.0-expressive`（开启 cot 解析时建议填写） |
| `req_params.audio_params.format` | 本项目固定 `mp3` |
| `req_params.audio_params.sample_rate` | 本项目 `24000` |
| `req_params.audio_params.speech_rate` | 语速偏移，整数：`(speed_ratio - 1) * 100` |
| `req_params.additions` | **JSON 字符串**（非对象），见下表 |

### 2.4 `additions` 常用字段（JSON 字符串内）

| 字段 | 类型 | 说明 |
|------|------|------|
| `model_type` | int | 复刻版本：`1` ICL1.0，`3` ICL1.0 并发，`4` ICL2.0 |
| `use_tag_parser` | bool | `true` 时解析 `<cot text="情感">文本</cot>` |
| `context_texts` | string[] | 未开 tag_parser 时用自然语言情感指令（仅首条生效） |

与 `.env` 对应关系：

| `.env` | 映射 |
|--------|------|
| `DOUBAO_CLONE_RESOURCE_ID` | 请求头 `X-Api-Resource-Id` |
| `DOUBAO_USE_TAG_PARSER` | `additions.use_tag_parser` |
| `DOUBAO_TTS_MODEL` | `req_params.model` |

---

## 3. Resource-Id 与 speaker 配对

| 音色 | `speaker` 示例 | `X-Api-Resource-Id` | `additions.model_type` |
|------|----------------|---------------------|-------------------------|
| 声音复刻 ICL 2.0 | `S_SUcfpOs32` | `seed-icl-2.0` | `4` |
| 声音复刻 ICL 1.0 并发 | `S_xxx` | `seed-icl-1.0-concurr` | `3` |
| 声音复刻 ICL 1.0 | `S_xxx` | `seed-icl-1.0` | `1` |
| 大模型 2.0 音色 | `zh_female_*_bigtts` 等 | `seed-tts-2.0` | 可不填或按文档 |

**错误 `InvalidModelType` / Resource id mismatched**：多为 Resource-Id 与音色训练版本不一致。已在 `.env` 指定 `DOUBAO_CLONE_RESOURCE_ID` 时，本项目**不再**自动回退到 1.0，避免掩盖真实错误。

---

## 4. 响应：NDJSON 流式解析

响应为多行 JSON（NDJSON），每行一个事件。本项目 `_parse_v3_ndjson_body()` 逻辑：

| `code` | 含义 | 处理 |
|--------|------|------|
| `0` 或 `3000` | 音频分片 | `data` 字段为 base64，解码后拼接 |
| `20000000` | 合成结束 | 停止读取 |
| 其他 | 错误 | 取 `message` 抛出 |

拼接后的二进制写入 `backend/static/audio/{uuid}.mp3`，对外 URL：

`{PUBLIC_BASE_URL}/static/audio/{filename}.mp3`

---

## 5. 直连 curl 示例（调官方接口）

将 `YOUR_API_KEY`、`S_音色`、`seed-icl-2.0` 换成控制台实际值：

```bash
curl -s -X POST 'https://openspeech.bytedance.com/api/v3/tts/unidirectional' \
  -H 'Content-Type: application/json' \
  -H 'X-Api-Key: YOUR_API_KEY' \
  -H 'X-Api-Resource-Id: seed-icl-2.0' \
  -H "X-Api-Request-Id: $(uuidgen)" \
  -d '{
    "user": {"uid": "debug"},
    "req_params": {
      "text": "<cot text=\"轻柔缓慢地哼唱歌谣，带旋律感\">潮声呢，低语吧。</cot>",
      "speaker": "S_SUcfpOs32",
      "model": "seed-tts-2.0-expressive",
      "audio_params": {"format": "mp3", "sample_rate": 24000, "speech_rate": -8},
      "additions": "{\"model_type\":4,\"use_tag_parser\":true}"
    }
  }'
```

经本项目网关（需先启动后端）：

```bash
curl -s -X POST 'http://127.0.0.1:8010/v1/tts' \
  -H 'Content-Type: application/json' \
  -d '{"text":"<cot text=\"平静\">博士，我在这里。</cot>","emotion":"gentle"}'
```

---

## 6. 代码映射（改接口时看这里）

| 功能 | 函数 / 常量 |
|------|-------------|
| 接口 URL | `DOUBAO_V3_URL` |
| 组包（复刻） | `_build_v3_clone_payload()` |
| 组包（大模型） | `_build_v3_standard_payload()` |
| 鉴权头 | `_v3_header_variants()` |
| 发送 + 解析 | `_post_v3_tts()` → `_parse_v3_ndjson_body()` |
| 对外入口 | `synthesize()`、`synthesize_sing()`（赠礼哼唱） |
| cot 文本 | `persona.prepare_tts_text()` |
| 赠礼链路 | `gift_events.trigger_gift_event()` |

旧版 V1 回退：`DOUBAO_V1_URL` = `https://openspeech.bytedance.com/api/v1/tts`（仅 `doubao_app_id` 鉴权场景）。

---

## 7. 相关官方文档

| 文档 | 链接 |
|------|------|
| **本文档对应的官方页** | [1598757 HTTP 单向 V3](https://www.volcengine.com/docs/6561/1598757?lang=zh#_2-http-chunked格式接口说明) |
| TTS 能力总览 | [162929](https://www.volcengine.com/docs/6561/162929?lang=zh) |
| API FAQ | [111586](https://www.volcengine.com/docs/6561/111586?lang=zh) |
| 产品简介 | [1594360](https://www.volcengine.com/docs/6561/1594360?lang=zh) |

项目内配置速查：[doubao-tts-setup.md](doubao-tts-setup.md) · 401 排障：[doubao-tts-401-fix.md](doubao-tts-401-fix.md)
