# Android 离线打包 — 自定义调试基座

本文按 DCloud 官方说明整理，对应问答：[android——离线打包制作自定义基座](https://ask.dcloud.net.cn/article/35482)。

适用场景：需要在 **Android Studio 本地** 打出带自定义图标/权限的调试 APK，再在 HBuilderX 里选「自定义调试基座」运行（不依赖 DCloud 云端制作基座）。

本项目路径：`ai-voice-chat/uniapp/`，AppID：`__UNI__F19B18B`（须与 [开发者中心](https://dev.dcloud.net.cn/) 一致）。

---

## 方式对比（先选对路线）

| 方式 | 操作 | 优点 | 缺点 |
|------|------|------|------|
| **云制作基座**（推荐多数情况） | HBuilderX：发行 → 制作自定义调试基座 | 无需 Android Studio；步骤少 | 需 DCloud 账号与排队 |
| **离线制作基座**（本文） | Android Studio + 离线 SDK 打 APK | 本地可控、可改原生工程 | 环境重；SDK 版本必须与 HBuilderX 一致 |

若仅需「浊心斯卡蒂」图标而非 HBuilder 绿标，优先见 [pack-android-ios.md §1.1](pack-android-ios.md#11-制作自定义调试基座详细步骤) 的 **云端基座**；本文是 **离线** 补充。

---

## 一、环境准备

1. **HBuilderX**（App 开发版）与 **Android 离线 SDK** 的 **主版本号必须一致**（例如均为 4.87）。不一致会出现「SDK 不一样，同步数据失败」——见 [35482 评论区](https://ask.dcloud.net.cn/article/35482)。
2. 从 [Android 离线 SDK 下载](https://nativesupport.dcloud.net.cn/AppDocs/download/android.html) 解压，记下路径，下文记为 `$ANDROID_SDK`。
3. 安装 **Android Studio**，JDK 8+。
4. 在 HBuilderX 打开 **`uniapp`** 目录，确认 `manifest.json` 中 AppID、图标、权限已保存（本项目已配麦克风与 `usesCleartextTraffic`）。
5. **Android 离线 AppKey**（否则真机弹窗「未配置 appkey 或配置错误」）：见 **[dcloud-android-appkey.md](dcloud-android-appkey.md)**，配置 `uniapp/dcloud-android.local.properties` 后再执行 `./scripts/build-android-debug-base.sh`。

---

## 二、配置离线 Android 工程

详细工程结构见：[Android 离线打包](https://nativesupport.dcloud.net.cn/AppDocs/usesdk/android.html)。自定义基座在标准离线工程上增加 **debug** 能力。

### 2.1 导入与 AppID

1. 用 Android Studio 打开离线 SDK 中的示例工程（一般为 `HBuilder-Integrate-AS` 或文档指定 module）。
2. 将 **dcloud_control.xml** / **manifest** 中的 AppID 改为与本项目一致：`__UNI__F19B18B`。
3. 把 HBuilderX 生成本地打包资源后得到的 `apps/__UNI__F19B18B/www`（或发行 → 生成本地打包 App 资源）同步到 Android 工程的 `assets/apps/` 下（与官方离线文档步骤相同）。

### 2.2 开启 debug（35482 要求）

在工程根或 app 模块的 **gradle 配置** 中，将根节点 **`debug`** 与 **`syncDebug`** 设为 **`true`**（具体节点名以当前离线 SDK 自带 `build.gradle` 注释为准，在 AS 中搜索 `syncDebug`）。

### 2.3 依赖库

在 **app 模块** `build.gradle` 的 `dependencies` 中增加（[35482](https://ask.dcloud.net.cn/article/35482)）：

1. 从离线 SDK 中找到 **`debug-server-release.aar`**，按官方文档方式 `implementation files(...)` 或放入 `libs` 引用。
2. 增加：

```gradle
dependencies {
    // … 离线 SDK 原有依赖 …
    implementation "com.alibaba:fastjson:1.2.83"
    implementation "com.squareup.okhttp3:okhttp:3.12.12"
    implementation "net.lingala.zip4j:zip4j:2.11.5"
}
```

### 2.4 图标与名称

离线工程里的 **应用名、图标** 需与 `uniapp/manifest.json` → `distribute.icons` 一致；改 manifest 后应重新生成本地打包资源并拷贝到 `assets`，再重新 **assembleDebug**。

---

## 三、生成 APK

在 Android Studio 任选其一：

1. **Build → Build Bundle(s) / APK(s) → Build APK(s)**（Debug）。
2. 右侧 **Gradle** → 对应 module → **Tasks → build → assembleDebug**。

产物一般在：

- `HBuilder-Integrate-AS` 工程：`simpleDemo/build/outputs/apk/debug/simpleDemo-debug.apk`
- 其他示例工程可能为：`app/build/outputs/apk/debug/app-debug.apk`

（以 Project 视图下的 `build` 目录为准。）

本仓库一键脚本（需已用 HBuilderX 5.07 生成本地打包资源）：

```bash
./scripts/build-android-debug-base.sh
```

---

## 四、复制到 HBuilderX 项目（35482 核心步骤）

在本仓库执行（会自动创建目录）：

```bash
cd uniapp
./scripts/setup-debug-base-dir.sh
# 将 Android Studio 生成的 debug APK 复制并重命名：
cp /path/to/app-debug.apk unpackage/debug/android_debug.apk
```

**目录结构必须为：**

```text
uniapp/
  unpackage/
    debug/
      android_debug.apk    ← 文件名固定，不可改
```

说明：

- `unpackage/` 已在 `.gitignore` 中，APK 不提交 Git，仅本机使用。
- 若为 **npm / CLI 工程** 且运行目录在 `dist`，部分版本需放在 `dist/debug/android_debug.apk`；本项目用 HBuilderX 打开 **`uniapp` 根目录**，用 **`unpackage/debug/`** 即可。

---

## 五、在 HBuilderX 使用自定义基座

参考：[什么是自定义基座及使用说明](https://uniapp.dcloud.net.cn/tutorial/run/run-app.html#customplayground)

1. 卸载手机上旧的 **绿色 HBuilder 标准基座**。
2. 菜单：**运行 → 运行到手机或模拟器 → 运行基座选择 → 自定义调试基座**。
3. 选择安卓真机，首次会安装 `android_debug.apk`，桌面应显示 **浊心斯卡蒂** 与项目图标。
4. 之后改 `.vue` / `.js`：直接「运行到手机」热更新；**仅当修改 manifest 图标、权限、原生模块时** 需重新打 APK 并覆盖 `android_debug.apk`。

---

## 六、与本项目相关的检查清单

| 项 | 值 / 位置 |
|----|-----------|
| HBuilderX 打开目录 | `ai-voice-chat/uniapp` |
| AppID | `__UNI__F19B18B` |
| 应用名 | 浊心斯卡蒂 |
| 图标 | `static/icons/*.png`（可运行 `scripts/generate-icons.sh`） |
| 内网 HTTP | `usesCleartextTraffic: true` |
| 基座 APK 路径 | `uniapp/unpackage/debug/android_debug.apk` |

---

## 七、常见问题

| 现象 | 处理 |
|------|------|
| SDK 不一样 / 同步数据失败 | HBuilderX 与下载的 **离线 SDK 同版本**；重新下载 SDK 并重打 APK |
| 仍是绿色 H、名称为 HBuilder | 运行基座选成了「标准基座」；或 `android_debug.apk` 未放到 `unpackage/debug/` |
| 请求的页面 `__uniappview.html` 无法打开 | AppID 或 `www` 资源未正确放入离线工程 assets |
| 修改图标不生效 | 更新 manifest → 生成本地打包资源 → 重新 assembleDebug → 覆盖 `android_debug.apk` → 卸载旧 App |

---

## 八、参考链接

- [35482 离线打包制作自定义基座](https://ask.dcloud.net.cn/article/35482)
- [Android 离线打包](https://nativesupport.dcloud.net.cn/AppDocs/usesdk/android.html)
- [Android 离线 SDK 下载](https://nativesupport.dcloud.net.cn/AppDocs/download/android.html)
- 本项目云基座步骤：[pack-android-ios.md](pack-android-ios.md)
