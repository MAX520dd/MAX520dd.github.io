#!/bin/bash
# 双击此文件即可启动后端（macOS）；关闭窗口或 Ctrl+C 会停止服务
cd "$(dirname "$0")"

stop_all() {
  if [[ -n "${BACKEND_PID:-}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo ""
    echo "正在停止后端..."
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap stop_all EXIT INT TERM HUP

./start-backend.sh &
BACKEND_PID=$!
wait "$BACKEND_PID" 2>/dev/null || true

echo ""
read -n 1 -s -r -p "后端已停止。按任意键关闭此窗口..."
