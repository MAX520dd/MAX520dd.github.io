#!/usr/bin/env bash
# 生成本地配置文件（不进入 Git）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ ! -f "$ROOT/backend/.env" ]]; then
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  echo "已创建 backend/.env，请填入 API Key 与 PUBLIC_BASE_URL"
fi

if [[ ! -f "$ROOT/uniapp/config/server.local.js" ]]; then
  cp "$ROOT/uniapp/config/server.example.js" "$ROOT/uniapp/config/server.local.js"
  echo "已创建 uniapp/config/server.local.js，请改成手机可访问的 Mac IP:8010"
else
  echo "已存在 uniapp/config/server.local.js，未覆盖"
fi

LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)
if [[ -n "$LAN_IP" ]]; then
  echo "提示：可将 PUBLIC_BASE_URL 与 AUTO_SERVER_URL 设为 http://${LAN_IP}:8010"
fi
