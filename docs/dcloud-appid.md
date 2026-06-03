# DCloud AppID 配置说明

云打包、自定义调试基座会报错 **「appid 不存在，请在 manifest.json 中重新获取」**，说明当前 `manifest.json` 里的 AppID **未在 DCloud 开发者中心登记**。

本项目原先的 `__UNI__AIVOICECHAT` 仅为本地占位，**不能**直接用于打包。

## 方法一：在 HBuilderX 中重新获取（推荐）

1. 用 HBuilderX 打开 **`ai-voice-chat/uniapp`**
2. 双击 **`manifest.json`**，切换到 **「基础配置」** 可视化页
3. 找到 **AppID** 一行，点击右侧 **「重新获取」**（或 DCloud 图标）
4. 登录 DCloud 账号（无账号则先注册：https://dev.dcloud.net.cn/）
5. 选择 **「创建新应用」**（或绑定已有应用）
   - 应用名称可填：`浊心斯卡蒂`
6. 成功后 AppID 会自动变成类似 **`__UNI__G1A2B3C4`** 的正式 ID（由平台分配）
7. **保存** `manifest.json`（Ctrl/Cmd + S）
8. 再执行：**发行 → 原生 App-制作自定义调试基座** 或 **云打包**

## 方法二：在网页开发者中心创建

1. 打开 https://dev.dcloud.net.cn/
2. 登录 → **应用管理** → **创建应用**
3. 应用名称：`浊心斯卡蒂`；类型选 **uni-app**
4. 创建后复制 **AppID**（`__UNI__` 开头）
5. 在 HBuilderX 打开 `uniapp/manifest.json`，把 `appid` 字段改成复制的值并保存

## 检查是否成功

- `manifest.json` 中 `appid` 为 **`__UNI__` + 平台分配的字母数字**（不是手写任意字符串）
- HBuilderX 右上角已登录 **同一 DCloud 账号**
- 云打包 / 制作基座时不再提示 appid 不存在

## Android 离线自定义基座：AppKey

离线打包（Android Studio 打 `android_debug.apk`）还需配置 **Android 离线 Key**，与 AppID 不是同一个东西。  
见 **[dcloud-android-appkey.md](dcloud-android-appkey.md)**。

## 注意

- AppID 与项目绑定后，**不要随意改成别的项目的 ID**
- 换电脑开发时，用同一 DCloud 账号登录即可
- 微信小程序的 `mp-weixin.appid` 是另一套微信 AppID，与 DCloud AppID 无关
