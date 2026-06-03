#!/usr/bin/env bash
# 项目根目录一键启动后端
cd "$(dirname "$0")/backend"
chmod +x run.sh 2>/dev/null || true
./run.sh
