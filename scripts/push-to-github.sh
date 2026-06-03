#!/usr/bin/env bash
# 在本机终端运行（Cursor 终端或 iTerm），勿把 Token 发给他人或 AI
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "错误：当前目录不是 Git 仓库"
  exit 1
fi

AHEAD=$(git rev-list --left-right --count origin/main...main 2>/dev/null | awk '{print $2}' || echo "?")
echo "本地 main 领先 origin/main 约 ${AHEAD} 个提交"
echo ""
echo "需要 GitHub Classic Token，且勾选 repo 权限："
echo "  https://github.com/settings/tokens"
echo ""

read -r -p "GitHub 用户名 [MAX520dd]: " GH_USER
GH_USER="${GH_USER:-MAX520dd}"
read -r -s -p "粘贴 Token（输入不可见）: " GH_TOKEN
echo ""

if [[ -z "$GH_TOKEN" ]]; then
  echo "未输入 Token，已取消"
  exit 1
fi

export GIT_TERMINAL_PROMPT=0
git push "https://${GH_USER}:${GH_TOKEN}@github.com/MAX520dd/MAX520dd.github.io.git" main
git branch -u origin/main main 2>/dev/null || true

echo ""
echo "推送完成。请到 https://github.com/MAX520dd/MAX520dd.github.io 确认"
echo "建议立即在 GitHub 撤销刚使用的 Token（若曾泄露）并重新生成。"
