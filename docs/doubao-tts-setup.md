# 豆包语音 TTS 配置说明

## 官方文档（排障优先查阅）

| 说明 | 链接 |
|------|------|
| **TTS 总览 / 能力说明（本项目主索引）** | [豆包语音文档 162929](https://www.volcengine.com/docs/6561/162929?lang=zh) |
| HTTP 单向流式 V3（当前接入） | [1598757](https://www.volcengine.com/docs/6561/1598757?lang=zh) |
| API 接入 FAQ | [111586](https://www.volcengine.com/docs/6561/111586?lang=zh) |
| 产品文档首页 | [6561](https://www.volcengine.com/docs/6561?lang=zh) |

遇 `InvalidModelType`、Resource-Id 不匹配、鉴权失败、哼唱/情感 cot 无效等问题，先查 **162929** 及上表对应章节，再对照下文 `.env` 与 `backend/services/tts_doubao.py`。

## 新版控制台（推荐）

火山语音新版控制台已废弃「应用管理 + AppID」，API 接入统一使用 **API Key**。

| 控制台位置 | `.env` 变量 | 请求头 |
|------------|-------------|--------|
| [API Key 管理](https://console.volcengine.com/speech) → **API Key** | `DOUBAO_API_KEY` | `X-Api-Key` |

```env
DOUBAO_API_KEY=your-api-key
DOUBAO_VOICE_TYPE=S_SUcfpOs32
DOUBAO_CLONE_RESOURCE_ID=seed-icl-2.0
DOUBAO_USE_TAG_PARSER=true
DOUBAO_TTS_MODEL=seed-tts-2.0-expressive
```

`DOUBAO_ACCESS_TOKEN` 与 `DOUBAO_API_KEY` **等价**。

官方文档：[HTTP 单向流式 V3](https://www.volcengine.com/docs/6561/1598757)

## 单向 HTTP：情感标签（cot 解析）

适用于 **声音复刻大模型 2.0 表现力版**（非默认 `standard`，standard 会忽略 cot）。

### 请求要求

| 字段 | 值 |
|------|-----|
| 接口 | `POST https://openspeech.bytedance.com/api/v3/tts/unidirectional` |
| `req_params.model` | `seed-tts-2.0-expressive` |
| `req_params.additions` | JSON 字符串，含 `"use_tag_parser": true` 与 `"model_type": 4`（ICL2.0） |
| `X-Api-Resource-Id` | `seed-icl-2.0`（与复刻训练版本一致） |

### 文本格式（写在 `req_params.text`）

```text
<cot text="用开心的语气">今天过得不错。</cot>
```

多组示例：

```text
<cot text="急促难耐">工作占据了生活的绝大部分</cot>，<cot text="语速缓慢">只有去做伟大的工作，才能获得满足感。</cot>
```

注意：

- 标签内 **text 属性** 写情感/语速描述，**标签内** 写要朗读的对白
- 单句（含标签）建议 **&lt; 64 字**
- cot 标签文本 **不计费**
- 不要用旧式 `<cot>描述</cot>对白`（本项目会自动转换，但推荐 LLM 直接写 text= 格式）

### 本项目自动处理

- 聊天气泡：去掉 cot，只显示对白；`stage_direction` 展示 text 属性
- 合成：`prepare_tts_text` 生成官方格式；`additions.use_tag_parser=true`
- 关闭 cot 解析：`DOUBAO_USE_TAG_PARSER=false`，改回 `additions.context_texts`
- 角色扮演括号：仅全角（…）表不可念出的旁白；`extract_paren_asides` 剥离后写入聊天气泡下方 `stage`，`strip_paren_from_raw` 后的 cot 对白才送 TTS（见 `llm_client.py`）

## 复刻音色（S_ 开头）

| 训练版本 | `DOUBAO_CLONE_RESOURCE_ID` | `additions.model_type` |
|----------|----------------------------|------------------------|
| ICL 2.0（推荐） | `seed-icl-2.0` | `4` |
| ICL 1.0 并发 | `seed-icl-1.0-concurr` | `3` |
| ICL 1.0 | `seed-icl-1.0` | `1` |

## 测试

```bash
curl -X POST http://127.0.0.1:8000/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"博士，我在这里呢。","emotion":"gentle"}'
```

`/health?check_tts=true` 可实测鉴权。
