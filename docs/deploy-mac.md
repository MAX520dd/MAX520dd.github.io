# Mac 服务端部署指南

## 环境要求

- macOS 12+
- Python 3.10 或 3.11（推荐 3.11）
- 约 4GB 磁盘（SenseVoice 模型首次下载）
- 火山引擎豆包语音 **API Key**（控制台 → API Key 管理）
- 火山方舟 API Key（豆包大模型，用于人物性格对话）

## 1. 安装依赖

```bash
cd ai-voice-chat/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> SenseVoice 依赖 `torch`，首次安装较慢。若仅需调试 LLM+TTS，可在 `.env` 设置 `ASR_ENABLED=false`，客户端用文本输入。

## 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`：

| 变量 | 说明 |
|------|------|
| `LLM_API_KEY` | 火山方舟 API 密钥 |
| `LLM_BASE_URL` | `https://ark.cn-beijing.volces.com/api/v3`（以控制台地域为准） |
| `LLM_MODEL` | **推理接入点 ID**，形如 `ep-xxxxxxxxxx-xxxxx`（见下方创建步骤） |
| `LLM_TEMPERATURE` | 人物口语多样性，推荐 `0.9` |
| `LLM_MAX_TOKENS` | 限制回复长度，推荐 `256`（利于 TTS 短句） |
| `LLM_TOP_P` | 可选，推荐 `0.9` |
| `DOUBAO_API_KEY` | 豆包语音 API Key（`X-Api-Key`，见 [配置说明](doubao-tts-setup.md)） |
| `DOUBAO_ACCESS_TOKEN` | 与 `DOUBAO_API_KEY` 等价，兼容旧 `.env` |
| `DOUBAO_VOICE_TYPE` | 默认音色 ID（复刻音色如 `S_SUcfpOs32`） |
| `PUBLIC_BASE_URL` | 手机可访问的 Mac 地址，如 `http://192.168.1.100:8010` |

### 创建火山方舟推理接入点（人物性格推荐）

1. 打开 [火山方舟控制台](https://console.volcengine.com/ark)
2. 进入 **在线推理** → **创建推理接入点**
3. 模型选择（二选一）：
   - **质量优先**：Doubao-Seed-1.6 或 Doubao-1.5-Pro
   - **省钱低延迟**：Doubao-Seed-1.6-Flash 或 Doubao-1.5-Lite
4. 避免选择带 **Thinking** 的模型（与 `think: false` 配置冲突）
5. 创建完成后复制 **接入点 ID**（`ep-xxx`）填入 `LLM_MODEL`
6. 在 API Key 管理创建密钥，填入 `LLM_API_KEY`

**重要**：`PUBLIC_BASE_URL` 必须填手机能访问的内网 IP，否则返回的音频 URL 手机无法播放。

## 3. 启动服务

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8010
```

浏览器打开 http://127.0.0.1:8010/health 应返回 `status: ok`。

## 4. 内网访问

1. 系统设置 → 网络 → 查看 Mac 的 WiFi IP（如 `192.168.1.100`）
2. 将 `.env` 中 `PUBLIC_BASE_URL` 改为 `http://192.168.1.100:8010`
3. 手机连接同一 WiFi，在 App 设置页填写相同地址（或配置 `uniapp/config/server.local.js`）
4. 若无法访问，检查 macOS 防火墙是否放行 8010 端口

## 5. 外出使用（内网穿透）

可选方案：

- **Tailscale**：Mac 与手机加入同一 Tailnet，用 Mac 的 Tailscale IP
- **frp / ngrok**：将 8010 映射到公网 HTTPS 域名，App 填穿透地址

穿透后请将 `PUBLIC_BASE_URL` 改为外网可访问的完整 URL。

## 6. API 自测

```bash
# 健康检查
curl http://127.0.0.1:8010/health

# 文本对话
curl -X POST http://127.0.0.1:8010/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"你好","persona_id":"skadi"}'

# TTS
curl -X POST http://127.0.0.1:8010/v1/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，很高兴认识你"}'
```

## 7. 常见问题

| 现象 | 处理 |
|------|------|
| ASR 报错 / 503 | 确认 `funasr` 安装成功；或 `ASR_ENABLED=false` 用文本 |
| TTS 失败 | 检查 `DOUBAO_API_KEY`、音色 ID 是否在控制台开通；`/health?check_tts=true` |
| 手机播不了音频 | 检查 `PUBLIC_BASE_URL` 是否为手机可达 IP |
| LLM 返回思考内容 | 服务端已过滤 think 标签；确认 provider 支持 `think: false` |
