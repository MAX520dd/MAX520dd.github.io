#!/usr/bin/env bash
# 将 uniapp/static/icons 同步到离线 SDK 的 simpleDemo 原生图标（打自定义基座前可单独执行）
set -euo pipefail

UNIAPP="$(cd "$(dirname "$0")/.." && pwd)"
SDK_ROOT="${ANDROID_SDK_ROOT:-/Users/mac/Downloads/最新版/5.07/Android-SDK@5.07.82603_20260414}"
RES="$SDK_ROOT/HBuilder-Integrate-AS/simpleDemo/src/main/res"
ICON_DIR="$UNIAPP/static/icons"

if [[ ! -f "$ICON_DIR/192x192.png" ]]; then
  echo "请先: cd uniapp && ./scripts/generate-icons.sh static/icon-source.jpg"
  exit 1
fi

cp "$ICON_DIR/192x192.png" "$RES/drawable/icon.png"
sips -Z 1280 "$ICON_DIR/1024x1024.png" --out "$RES/drawable/splash.png" >/dev/null
echo "已更新: $RES/drawable/icon.png, splash.png"
echo "应用名请在 strings.xml 中为「浊心斯卡蒂」"
echo "然后执行: ../../scripts/build-android-debug-base.sh"
