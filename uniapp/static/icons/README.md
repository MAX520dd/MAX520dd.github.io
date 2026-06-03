# 应用图标

源图：`static/icon-source.jpg`（或任意 1024×1024 方图）

重新生成各尺寸：

```bash
cd uniapp
./scripts/generate-icons.sh static/icon-source.jpg
```

`manifest.json` → `app-plus.distribute.icons` 已指向本目录。

**注意：** 用 HBuilderX「运行到手机」且桌面显示 **HBuilder** 绿色 H 图标时，是**标准调试基座**，不会用这里的图标。请使用 **自定义调试基座** 或 **云打包** 安装包。详见 `docs/pack-android-ios.md`。

**更换图标后（离线自定义基座）：**

1. 替换 `static/icon-source.jpg`（建议 1024×1024 方图）
2. `./scripts/generate-icons.sh static/icon-source.jpg`
3. HBuilderX：**发行 → 生成本地打包 App 资源**（刷新 `www` 内图标）
4. 项目根：`./scripts/build-android-debug-base.sh`（会同步原生 `icon.png` / `splash.png` 并重打 APK）
5. 卸载旧 App，HBuilderX 选 **自定义调试基座** 再运行
