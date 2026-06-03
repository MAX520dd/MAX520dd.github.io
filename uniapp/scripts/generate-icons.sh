#!/usr/bin/env bash
# 从一张 1024×1024 方图重新生成各尺寸应用图标
set -e
cd "$(dirname "$0")/.."
SRC="${1:-../assets/icon-source.png}"
DST="static/icons"
if [ ! -f "$SRC" ]; then
  echo "用法: ./scripts/generate-icons.sh <源图路径>"
  exit 1
fi
mkdir -p "$DST"
sips -s format png "$SRC" --out "$DST/1024x1024.png" >/dev/null
for size in 72 96 144 192 120 180 40 60 58 87 80; do
  sips -z "$size" "$size" "$DST/1024x1024.png" --out "$DST/${size}x${size}.png" >/dev/null
done
echo "已生成到 $DST/"
