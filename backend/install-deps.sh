#!/usr/bin/env bash
# 使用国内镜像安装依赖
set -e
cd "$(dirname "$0")"

# 清华源（可改为 aliyun: https://mirrors.aliyun.com/pypi/simple/）
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
PIP_HOST="pypi.tuna.tsinghua.edu.cn"

echo "使用镜像: ${PIP_INDEX}"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

python -m pip install --upgrade pip -i "${PIP_INDEX}" --trusted-host "${PIP_HOST}"

echo "[1/2] 安装核心依赖..."
pip install -r requirements-core.txt -i "${PIP_INDEX}" --trusted-host "${PIP_HOST}"

ASR_ENABLED=true
if [ -f .env ]; then
  val=$(grep -E '^ASR_ENABLED=' .env | cut -d= -f2 | tr '[:upper:]' '[:lower:]' | tr -d ' ')
  [ "$val" = "false" ] && ASR_ENABLED=false
fi

if [ "$ASR_ENABLED" = "true" ]; then
  echo "[2/2] 安装 ASR 依赖（torch 较大，请耐心等待）..."
  pip install -r requirements-asr.txt -i "${PIP_INDEX}" --trusted-host "${PIP_HOST}" || {
    echo "[警告] ASR 依赖安装失败，可在 .env 设置 ASR_ENABLED=false 后仅使用文字聊天"
  }
else
  echo "[2/2] 跳过 ASR（.env 中 ASR_ENABLED=false）"
fi

touch .venv/.deps_installed
echo "依赖安装完成。"
