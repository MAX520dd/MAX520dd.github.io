#!/usr/bin/env bash
# 按 https://ask.dcloud.net.cn/article/35482 创建自定义基座 APK 放置目录
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/unpackage/debug"
mkdir -p "$DIR"
cat > "$DIR/README.txt" <<'EOF'
将 Android Studio 离线打包生成的 Debug APK 复制到此目录，并命名为：

  android_debug.apk

然后在 HBuilderX：运行 → 运行到手机 → 运行基座选择 → 自定义调试基座。

详见项目文档：docs/android-offline-custom-base.md
EOF
echo "已创建: $DIR"
echo "请将离线 debug APK 复制为: $DIR/android_debug.apk"
