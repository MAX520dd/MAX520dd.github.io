#!/usr/bin/env bash
# 离线 SDK 打自定义调试基座 → 复制到 uniapp/unpackage/debug/android_debug.apk
# 需：Android SDK、与本项目 HBuilderX 5.07 一致的离线 SDK
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UNIAPP="$ROOT/uniapp"
SDK_ROOT="${ANDROID_SDK_ROOT:-/Users/mac/Downloads/最新版/5.07/Android-SDK@5.07.82603_20260414}"
AS="$SDK_ROOT/HBuilder-Integrate-AS"
APPID="__UNI__F19B18B"
WWW_SRC="$UNIAPP/unpackage/resources/${APPID}/www"

if [[ ! -d "$AS" ]]; then
  echo "未找到离线工程: $AS"
  echo "请设置 ANDROID_SDK_ROOT 或修改本脚本中的 SDK_ROOT"
  exit 1
fi

if [[ ! -f "$WWW_SRC/manifest.json" ]]; then
  echo "缺少本地打包资源: $WWW_SRC"
  echo "请在 HBuilderX 打开 uniapp → 发行 → 生成本地打包 App 资源（5.07）"
  exit 1
fi

APPKEY_FILE="$UNIAPP/dcloud-android.local.properties"
if [[ ! -f "$APPKEY_FILE" ]]; then
  echo "缺少 AppKey 配置: $APPKEY_FILE"
  echo "  cp uniapp/dcloud-android.local.properties.example uniapp/dcloud-android.local.properties"
  echo "  按 docs/dcloud-android-appkey.md 从 dev.dcloud.net.cn 复制 Android 离线 Key"
  exit 1
fi
# shellcheck disable=SC1090
source "$APPKEY_FILE"
if [[ -z "${DCLOUD_APPKEY:-}" ]]; then
  echo "请在 $APPKEY_FILE 中设置 DCLOUD_APPKEY=（开发者中心 → 查看离线 Key）"
  exit 1
fi

MANIFEST="$AS/simpleDemo/src/main/AndroidManifest.xml"
echo "==> 写入 dcloud_appkey 到 AndroidManifest.xml"
sed -i '' '/android:name="dcloud_appkey"/{
n
s|android:value="[^"]*"|android:value="'"$DCLOUD_APPKEY"'"|
}' "$MANIFEST"

ICON_DIR="$UNIAPP/static/icons"
if [[ ! -f "$ICON_DIR/192x192.png" ]]; then
  echo "缺少应用图标，请先执行:"
  echo "  cd uniapp && ./scripts/generate-icons.sh static/icon-source.jpg"
  exit 1
fi

echo "==> 同步桌面图标 / 启动图到 simpleDemo（原生 res）"
RES_DRAWABLE="$AS/simpleDemo/src/main/res/drawable"
cp "$ICON_DIR/192x192.png" "$RES_DRAWABLE/icon.png"
# 启动图：由 1024 方图缩放到合适高度
sips -Z 1280 "$ICON_DIR/1024x1024.png" --out "$RES_DRAWABLE/splash.png" >/dev/null

echo "==> 同步 debug-server-release.aar"
cp "$SDK_ROOT/SDK/libs/debug-server-release.aar" "$AS/simpleDemo/libs/"

echo "==> 同步 www 到 assets/apps/${APPID}"
rm -rf "$AS/simpleDemo/src/main/assets/apps/${APPID}"
mkdir -p "$AS/simpleDemo/src/main/assets/apps"
cp -R "$UNIAPP/unpackage/resources/${APPID}" "$AS/simpleDemo/src/main/assets/apps/"

ANDROID_SDK="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
if [[ ! -d "$ANDROID_SDK" ]]; then
  echo "未找到 Android SDK，请安装 Android Studio 或设置 ANDROID_HOME"
  exit 1
fi
echo "sdk.dir=$ANDROID_SDK" > "$AS/local.properties"

echo "==> assembleDebug"
cd "$AS"
chmod +x gradlew
./gradlew :simpleDemo:assembleDebug

APK="$AS/simpleDemo/build/outputs/apk/debug/simpleDemo-debug.apk"
DEST="$UNIAPP/unpackage/debug"
mkdir -p "$DEST"
cp "$APK" "$DEST/android_debug.apk"
echo "已生成: $DEST/android_debug.apk"
echo "HBuilderX: 运行 → 运行到手机 → 自定义调试基座"
