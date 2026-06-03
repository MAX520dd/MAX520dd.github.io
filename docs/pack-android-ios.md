# UniApp 安卓 / iOS 打包指南

## 准备工作

1. 安装 [HBuilderX](https://www.dcloud.io/hbuilderx.html)（正式版）
2. Mac 后端已启动，手机能访问 `/health`
3. 用 HBuilderX 打开项目目录：`ai-voice-chat/uniapp/`
4. **配置 DCloud AppID**（云打包 / 自定义基座必填）：见 [dcloud-appid.md](dcloud-appid.md)  
   若提示「appid 不存在」：在 `manifest.json` → 基础配置 → **重新获取**，不要用占位符 `__UNI__AIVOICECHAT`

## 一、运行调试

1. 菜单：运行 → 运行到手机或模拟器
2. 首次需连接真机并开启 USB 调试（安卓）或信任电脑（iOS）
3. 打开 App → **设置** → 填写 Mac 内网地址 → 测试连接
4. 返回聊天页：文本发送或按住说话

### 为什么桌面图标还是绿色「H」、名字叫 HBuilder？

这是 **HBuilder 标准调试基座**，不是最终安装包。标准基座固定使用 DCloud 默认图标，**不会**读取你项目里的 `static/icons/*.png`。

| 运行方式 | 桌面图标 / 名称 |
|----------|-----------------|
| 运行 → 运行到手机（标准基座） | 绿色 H，显示 **HBuilder** |
| 运行 → 运行到手机（**自定义调试基座**） | 可使用 `manifest.json` 里配置的图标 |
| 发行 → 原生 App-云打包 / 正式安装包 | 使用自定义图标，名称 **浊心斯卡蒂** |

**要在真机调试时看到自定义图标：**

1. 确认 `uniapp/static/icons/` 下已有各尺寸 PNG（无则执行 `cd uniapp && ./scripts/generate-icons.sh static/icon-source.jpg`）
2. HBuilderX：**发行 → 原生 App-制作自定义调试基座**（勾选与 manifest 一致的图标）
3. 基座制作完成后：**运行 → 运行到手机 → 选择「自定义调试基座」**（不要选标准基座）
4. 或直接 **发行 → 原生 App-云打包** 安装 APK/IPA，图标即为正式效果

修改图标后需 **重新制作基座或重新云打包**，并删除手机上旧的 HBuilder 调试 App 再安装。

## 1.1 制作自定义调试基座（详细步骤）

在 HBuilderX 中请打开 **`ai-voice-chat/uniapp`** 目录（左侧项目根目录应是 `uniapp`，能看到 `manifest.json`）。

### 第一步：检查 manifest

1. 双击 `manifest.json` → 打开可视化配置
2. **基础配置**：应用名称应为「浊心斯卡蒂」；AppID 为 `__UNI__AIVOICECHAT`（须与 [DCloud 开发者中心](https://dev.dcloud.net.cn/) 里创建的应用一致）
3. **App 图标配置**（或「安卓/iOS 图标」）：确认各尺寸已指向 `static/icons/`，预览能见到角色图  
   - 若为空：终端执行 `cd uniapp && ./scripts/generate-icons.sh static/icon-source.jpg` 后，在 manifest 里重新点选图标路径
4. **App 模块配置**：本项目暂无需额外原生模块，保持默认即可
5. 保存 `manifest.json`（Ctrl/Cmd + S）

### 第二步：云端制作基座

1. 菜单：**发行 → 原生 App-制作自定义调试基座**  
   （部分版本文案为 **发行 → App 原生 App-制作自定义调试基座**）
2. 使用 DCloud 账号登录（右上角未登录会先提示登录）
3. 打包平台：勾选 **Android**（调试安卓机）或 **iOS**（需 Apple 证书，与正式包类似）
4. 证书：
   - **Android 测试**：可用「使用 DCloud 公用证书」
   - **iOS**：需选择开发证书 / 描述文件（与云打包相同）
5. 其他选项保持默认即可；图标、启动图、权限会从当前 `manifest.json` 读取
6. 点击 **打包**，等待云端完成（数分钟～十几分钟，控制台有进度）
7. 完成后可在 **发行 → 查看云打包状态** 下载基座 APK（可选，真机也会自动装）

> 修改了 **图标、启动图、权限、原生模块** 后，必须 **重新制作一次** 自定义基座，仅「运行」不会更新基座里的图标。

### 第三步：用自定义基座运行

1. **先删掉** 手机上旧的绿色 **HBuilder** 标准基座（长按卸载），避免装错 App
2. 菜单：**运行 → 运行到手机或模拟器 → 运行基座选择 → 自定义调试基座**  
   （不要选「标准基座」）
3. 再选你的安卓机 / 模拟器
4. 首次会把自定义基座安装到手机，桌面应显示 **浊心斯卡蒂** 和你的图标
5. 之后改 `.vue` / `.js` 代码：直接 **运行到手机** 即可热更新，**不必**每次重做基座；只有改 `manifest` 原生项时才重做基座

### 常见问题

| 现象 | 处理 |
|------|------|
| 菜单里没有「制作自定义调试基座」 | 确认打开的是 **uniapp** 目录；使用 HBuilderX **App 开发版**（非纯 Web 版） |
| 打包失败 AppID 不一致 | 登录 dev.dcloud.net.cn，创建应用，把 AppID 改成与 manifest 一致 |
| 运行后仍是绿色 H | 运行基座选成了「标准基座」；或未完成基座打包 |
| 图标还是旧的 | 重新 `generate-icons.sh` → 保存 manifest → **重新制作自定义基座** → 卸载旧 App 再运行 |

不想做基座时，可直接 **发行 → 原生 App-云打包** 装 APK，图标与名称与正式包一致。

### 1.2 离线 Android Studio 制作基座（可选）

若不用云端「制作自定义调试基座」，可在本机用 **Android 离线 SDK** 打出 Debug APK，放到 `uniapp/unpackage/debug/android_debug.apk`，再在 HBuilderX 选「自定义调试基座」。步骤见：

- **[android-offline-custom-base.md](android-offline-custom-base.md)**（对照 [DCloud 问答 35482](https://ask.dcloud.net.cn/article/35482)）
- 创建目录：`cd uniapp && chmod +x scripts/setup-debug-base-dir.sh && ./scripts/setup-debug-base-dir.sh`

**注意：** 离线 SDK 版本必须与 HBuilderX 一致，否则真机调试会报 SDK 不一致。

## 二、安卓 APK 打包

1. 菜单：发行 → 原生 App-云打包（或本地打包）
2. 选择 **Android**
3. 使用 DCloud 公用证书（测试）或上传自有证书（正式发布）
4. 勾选需要的 CPU 架构（`arm64-v8a` 即可）
5. 打包完成后下载 APK，传到手机安装

### 安卓注意事项

- `manifest.json` 已配置 `usesCleartextTraffic: true`，允许 HTTP 内网调试
- 正式发布若使用 HTTPS，可关闭明文流量
- 需授予 **麦克风** 权限才能录音

## 三、iOS 打包

1. 需要 **Apple 开发者账号**（个人或公司）
2. 菜单：发行 → 原生 App-云打包 → 选择 **iOS**
3. 或：发行 → 原生 App-本地打包 → 生成本地打包 App 资源
4. 用 **Xcode** 打开 `uniapp/unpackage/.../Pandora...xcodeproj`
5. 配置 Signing & Capabilities → Team
6. 真机运行或 Product → Archive 上传 TestFlight / App Store

### iOS 注意事项

- `manifest.json` 已声明麦克风用途说明与后台音频 `UIBackgroundModes: audio`
- 内网 HTTP 需在 Xcode 的 Info.plist 配置 ATS 例外，或全程使用 HTTPS 穿透地址
- 录音建议在前台进行（系统对后台录音有限制）

## 四、配置清单（打包前检查）

| 项 | 位置 |
|----|------|
| 应用名称 | `manifest.json` → `name` |
| AppID | `manifest.json` → `appid`（云打包需与 DCloud 开发者中心一致） |
| 默认服务端 | `App.vue` onLaunch 或让用户在设置页填写 |
| 麦克风权限 | `manifest.json` → android permissions / ios privacyDescription |

## 五、发布建议

1. **居家使用**：仅配置内网 IP，无需上架应用商店
2. **外出使用**：配置 frp/Tailscale 后，在设置页切换外网地址
3. **隐私**：聊天记录仅存手机本地 `uni.storage`；ASR 在 Mac 本地；LLM/TTS 走云端需知悉

## 六、HBuilderX 常见问题

| 现象 | 处理 |
|------|------|
| 无法连接服务器 | 手机与 Mac 是否同 WiFi；IP 是否正确 |
| 录音无权限 | 系统设置中手动开启麦克风 |
| iOS 无法安装 | 检查证书与 Bundle ID |
| 音频不播放 | 确认 `PUBLIC_BASE_URL` 与 App 内服务端地址一致 |
