#!/usr/bin/env bash
# AI 语音对话 — 后端一键启动（Mac）
set -e
cd "$(dirname "$0")"

PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_HOST="pypi.tuna.tsinghua.edu.cn"

echo "=========================================="
echo "  AI 语音对话 · 后端服务"
echo "=========================================="

# 1. 检查 .env
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo "[提示] 未找到 .env，正在从 .env.example 复制..."
    cp .env.example .env
    echo "请编辑 backend/.env 填入密钥后重新运行。"
    exit 1
  else
    echo "[错误] 缺少 .env 配置文件"
    exit 1
  fi
fi

# 2. 简单检查必填项
check_env() {
  local key=$1
  local val
  val=$(grep -E "^${key}=" .env 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
  if [ -z "$val" ] || echo "$val" | grep -qE 'your-|xxxxx'; then
    echo "  [待填] ${key}"
    return 1
  fi
  return 0
}

MISS=0
check_env LLM_API_KEY || MISS=1
check_env LLM_MODEL || MISS=1
check_env DOUBAO_API_KEY || check_env DOUBAO_ACCESS_TOKEN || MISS=1
if [ "$MISS" -eq 1 ]; then
  echo ""
  echo "[警告] 上述配置未填写完整，服务可启动但对话/TTS 可能失败。"
  echo "编辑: $(pwd)/.env"
  echo ""
fi

# 3. Python 虚拟环境 + 国内镜像安装
need_install=false
if [ ! -d .venv ]; then
  need_install=true
elif [ ! -f .venv/.deps_installed ]; then
  need_install=true
fi

if [ "$need_install" = true ]; then
  echo "[安装] 使用清华镜像安装依赖（首次较慢）..."
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip -i "${PIP_INDEX}" --trusted-host "${PIP_HOST}"
  pip install -r requirements-core.txt -i "${PIP_INDEX}" --trusted-host "${PIP_HOST}"

  ASR_ENABLED=true
  val=$(grep -E '^ASR_ENABLED=' .env 2>/dev/null | cut -d= -f2 | tr '[:upper:]' '[:lower:]' | tr -d ' ')
  [ "$val" = "false" ] && ASR_ENABLED=false

  if [ "$ASR_ENABLED" = "true" ]; then
    echo "[安装] ASR 依赖（可选，失败可设 ASR_ENABLED=false）..."
    pip install -r requirements-asr.txt -i "${PIP_INDEX}" --trusted-host "${PIP_HOST}" || true
  fi
  touch .venv/.deps_installed
else
  source .venv/bin/activate
fi

# 4. 显示本机 IP
LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "")
PORT=$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo "8010")
PORT=${PORT:-8010}

port_in_use() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

if port_in_use "$PORT"; then
  echo "[错误] 端口 ${PORT} 已被占用（HBuilderX 常占 8000/8001）"
  lsof -nP -iTCP:"${PORT}" -sTCP:LISTEN 2>/dev/null || true
  echo "请编辑 backend/.env，将 PORT 改为 8010 或其他空闲端口（可用: lsof -i :8010）"
  exit 1
fi

echo ""
echo "  本机访问:  http://127.0.0.1:${PORT}"
echo "  健康检查:  http://127.0.0.1:${PORT}/health"
if [ -n "$LAN_IP" ]; then
  echo "  手机访问:  http://${LAN_IP}:${PORT}"
  echo "  建议在 .env 设置: PUBLIC_BASE_URL=http://${LAN_IP}:${PORT}"
fi
echo ""
echo "  按 Ctrl+C 或关闭此窗口停止服务"
echo "=========================================="
echo ""

_stopping=false
stop_server() {
  if [[ "$_stopping" == true ]]; then
    return
  fi
  _stopping=true
  echo ""
  echo "[停止] 正在关闭后端服务..."
  if [[ -n "${UVICORN_PID:-}" ]] && kill -0 "$UVICORN_PID" 2>/dev/null; then
    kill -TERM "$UVICORN_PID" 2>/dev/null || true
    pkill -P "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
  fi
}
trap stop_server EXIT INT TERM HUP

uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload &
UVICORN_PID=$!
wait "$UVICORN_PID" 2>/dev/null || true
