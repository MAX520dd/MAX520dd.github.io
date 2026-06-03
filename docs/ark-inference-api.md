# 火山方舟 · 在线推理 API 配置

## 环境变量（与终端 export 一致）

```bash
export ARK_API_KEY="ark-8d331c7e-fdb4-4c2c-91b0-0c96081105e5-6ef09"
```

或在 `backend/.env` 中：

```env
ARK_API_KEY=ark-8d331c7e-fdb4-4c2c-91b0-0c96081105e5-6ef09
LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_MODEL=ep-你的接入点ID
```

本项目 `LLM_API_KEY` 与 `ARK_API_KEY` 等价，任选其一即可。

## 接口地址

| 用途 | URL |
|------|-----|
| OpenAI SDK `base_url` | `https://ark.cn-beijing.volces.com/api/v3` |
| Chat Completions（curl 完整路径） | `https://ark.cn-beijing.volces.com/api/v3/chat/completions` |

请求头：

```
Authorization: Bearer <ARK_API_KEY>
Content-Type: application/json
```

## 获取 `LLM_MODEL`（ep- 接入点）

1. 打开 [在线推理 · 推理接入点](https://console.volcengine.com/ark/region:ark+cn-beijing/endpoint)
2. **创建推理接入点** → 选择 **Doubao-Seed-1.6** 或 **Doubao-1.5-Pro**
3. 复制名称以 `ep-` 开头的 ID，填入 `.env` 的 `LLM_MODEL`

## curl 自测（替换 ep 与 Key）

```bash
export ARK_API_KEY="ark-你的密钥"

curl https://ark.cn-beijing.volces.com/api/v3/chat/completions \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ep-你的接入点ID",
    "messages": [{"role": "user", "content": "今天好累啊"}],
    "temperature": 0.9,
    "max_tokens": 256
  }'
```

返回 `choices[0].message.content` 即成功。

## 与本项目的关系

```
UniApp → Mac FastAPI → OpenAI SDK
  base_url = LLM_BASE_URL
  api_key  = LLM_API_KEY 或 ARK_API_KEY
  model    = LLM_MODEL（ep-xxx）
```

启动后端：

```bash
cd backend && source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

`GET /health` 中 `llm_configured: true` 表示 Key 已配置；若对话仍失败，多半是 `LLM_MODEL` 未改成真实 `ep-xxx`。
