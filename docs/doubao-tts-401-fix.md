# 豆包 TTS 401 错误说明

## 错误现象

```
Client error '401 Unauthorized' for url 'https://openspeech.bytedance.com/api/v3/tts/unidirectional'
```

或提示 `authenticate request: load grant`。

## 原因

鉴权凭证错误或已过期。新版控制台应使用 **API Key**，不再依赖 AppID。

| 配置 | 说明 |
|------|------|
| `DOUBAO_API_KEY` | 推荐。语音控制台 → **API Key 管理** 复制 |
| `DOUBAO_APP_ID` + `DOUBAO_ACCESS_TOKEN` | 仅旧版应用管理账号回退 |

## 正确配置步骤（新版）

1. 打开 https://console.volcengine.com/speech
2. 进入 **API Key 管理** → 创建或复制 **API Key**
3. 写入 `backend/.env`：`DOUBAO_API_KEY=你的Key`
4. 重启后端 `./start-backend.sh`
5. 访问 `http://127.0.0.1:8000/health?check_tts=true`，确认 `tts_auth_ok: true`

## 复刻音色

`S_` 开头音色需已训练成功，且 `DOUBAO_CLONE_RESOURCE_ID` 与控制台训练版本一致（见 `docs/doubao-tts-setup.md`）。
