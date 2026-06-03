# 为斯卡蒂献上心脏 · AI 语音对话

面向《明日方舟》斯卡蒂 / 浊心斯卡蒂的 **角色扮演语音聊天** 实验项目：Mac 本地后端（FastAPI）+ UniApp 客户端，支持文字/语音对话、复刻音色 TTS、好感度与商城赠礼事件。

> 同人向个人作品，与鹰角网络无关。

## 功能概览

| 模块 | 说明 |
|------|------|
| 双角色 | 主线斯卡蒂（`skadi`）、浊心斯卡蒂（`skadi_corrupting`），独立人设、音色与头像 |
| 语音对话 | 火山方舟 LLM 生成台词 → 豆包声音复刻 TTS；可选 SenseVoice 本地 ASR |
| 对话表现 | `<cot>` 语气控制；全角括号 `（…）` 作旁白，仅显示在气泡下方、不送入 TTS |
| 罗德岛 Tab | 通信、干员名单、商城（合成玉/赠礼）、博士状态与特殊物品 |
| 赠礼事件 | 盐风城回忆、幽蓝潮声（哼唱）、大海之眠等，触发 LLM + TTS 剧情 |

## 技术栈

- **后端**：Python 3.11、FastAPI、火山方舟（LLM）、豆包语音 V3 TTS、可选 FunASR SenseVoice
- **前端**：UniApp（Vue 3），四 Tab + 微信式对话页
- **数据**：人设与商城目录在 `backend/data/*.json`；游戏进度存 App 本地 `uni.storage`

## 快速开始

### 1. 本地配置（首次必做，不入 Git）

```bash
cd ai-voice-chat
chmod +x scripts/setup-local-config.sh start-backend.sh backend/run.sh
./scripts/setup-local-config.sh
```

编辑 **`backend/.env`**（API Key、推理接入点、`PUBLIC_BASE_URL`）与 **`uniapp/config/server.local.js`**（与 `PUBLIC_BASE_URL` 相同的手机可访问地址）。  
模板见 `backend/.env.example`、`uniapp/config/server.example.js`。

### 2. 启动后端

```bash
./start-backend.sh
```

浏览器访问 http://127.0.0.1:8010/health ，`llm_configured`、`tts_configured` 应为 `true`。默认端口 **8010**（避免与 HBuilderX 占用 8000/8001）。

### 3. 运行 App

1. HBuilderX 打开 **`uniapp/`** 目录  
2. 运行到模拟器或 Android/iOS 真机（需自定义调试基座时见文档）  
3. 真机与 Mac 同一 WiFi；App 会尝试用 `server.local.js` 自动填服务地址，也可在「我」页设置中修改  

## 目录结构

```
ai-voice-chat/
├── backend/           # FastAPI：/v1/chat、/v1/tts、/v1/voice/chat、赠礼与人设 API
│   ├── data/          # personas.json、game_catalog.json、doctor_states.json
│   └── services/      # LLM、TTS、人设解析、好感度与赠礼
├── uniapp/            # UniApp 客户端
│   ├── config/        # server.example.js + 本地 server.local.js（gitignore）
│   └── pages/         # 对话、商城、干员、设置等
├── docs/              # 部署、TTS、打包说明
├── scripts/           # 本地配置脚本、Android 离线基座等
└── .cursor/skills/    # 人物性格编写 Skill（可选）
```

## 敏感信息与本地存储

以下内容 **不会** 提交到 Git（见 `.gitignore`）：

| 文件 | 内容 |
|------|------|
| `backend/.env` | 方舟 API Key、豆包 API Key、推理接入点、公网/局域网 `PUBLIC_BASE_URL` |
| `uniapp/config/server.local.js` | App 自动填入的后端地址 |
| `uni.storage`（真机） | 服务端地址、聊天记录、合成玉、好感度、背包等 |

克隆仓库后请执行 `./scripts/setup-local-config.sh` 自行生成本地文件。

## 文档

- [Mac 部署与联网](docs/deploy-mac.md)
- [豆包 TTS 配置（含官方文档索引）](docs/doubao-tts-setup.md)
- [方舟在线推理](docs/ark-inference-api.md)（若存在）
- [Android / iOS 打包与自定义基座](docs/pack-android-ios.md)（若存在）

## 角色音色（需在火山控制台开通）

| 角色 | 音色 ID |
|------|---------|
| 斯卡蒂 | `S_RUcfpOs32` |
| 浊心斯卡蒂 | `S_SUcfpOs32` |

在 `backend/data/personas.json` 的 `default_voice` 中配置。

## 许可证与声明

仅供学习与交流；请勿将 API Key 或复刻音色用于未授权商用。角色版权归 respective owners。

## 仓库

GitHub: [MAX520dd/MAX520dd.github.io](https://github.com/MAX520dd/MAX520dd.github.io)
