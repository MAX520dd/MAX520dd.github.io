# Android 离线打包 AppKey 配置

真机出现 **「未配置 appkey 或配置错误」**，说明离线工程 `AndroidManifest.xml` 里的 `dcloud_appkey` 未填写，或与 [开发者中心](https://dev.dcloud.net.cn/) 登记信息不一致。

官方说明：[申请 AppKey](https://nativesupport.dcloud.net.cn/AppDocs/usesdk/appkey.html)

## 本项目离线工程固定信息

| 项 | 值 |
|----|-----|
| AppID | `__UNI__F19B18B`（与 `manifest.json`、`dcloud_control.xml` 一致） |
| Android 包名 | `com.android.simple`（`simpleDemo/build.gradle` → `applicationId`） |
| 调试签名证书 | `HBuilder-Integrate-AS/simpleDemo/test.jks`（密码 `123456`，别名 `key0`） |
| 证书 SHA1 | `B6:BA:28:25:A2:68:43:01:34:B6:70:0C:B9:F1:DA:FF:DF:B5:B6:20` |

三者 **AppID + 包名 + SHA1** 必须与申请离线 Key 时填写的一致，否则校验失败。

## 操作步骤

### 1. 开发者中心配置 Android 平台

1. 登录 https://dev.dcloud.net.cn/
2. 打开应用 **浊心斯卡蒂**（AppID `__UNI__F19B18B`）
3. 进入 **各平台信息** → **Android** → **修改**（或创建）
4. 填写：
   - **包名**：`com.android.simple`
   - **SHA1**：`B6:BA:28:25:A2:68:43:01:34:B6:70:0C:B9:F1:DA:FF:DF:B5:B6:20`
   - （可选）SHA256：`60:3A:4C:5D:92:29:ED:6E:17:5E:2F:DD:62:4D:2F:D6:1C:13:F9:BA:8C:27:7B:ED:12:D0:3B:25:3D:DB:87:31`
5. 保存后点击 **查看离线 Key**，复制 **Android 离线 Key**（一串字母数字，**不是** AppID）

若你改了 `test.jks` 或 `applicationId`，需重新算 SHA1 并在后台更新后 **重新生成离线 Key**。

自行查看 SHA1：

```bash
keytool -list -v -keystore "/Users/mac/Downloads/最新版/5.07/Android-SDK@5.07.82603_20260414/HBuilder-Integrate-AS/simpleDemo/test.jks" -storepass 123456 -alias key0
```

### 2. 写入本项目（勿提交 Git）

```bash
cp uniapp/dcloud-android.local.properties.example uniapp/dcloud-android.local.properties
```

编辑 `uniapp/dcloud-android.local.properties`：

```properties
DCLOUD_APPKEY=这里粘贴开发者中心复制的Android离线Key
```

### 3. 重新打自定义基座

```bash
./scripts/build-android-debug-base.sh
```

脚本会把 AppKey 写入离线 `AndroidManifest.xml` 并生成 `uniapp/unpackage/debug/android_debug.apk`。

### 4. 手机端

1. 卸载旧 App  
2. HBuilderX：**运行 → 自定义调试基座**  

## 仍报错时排查

- `dcloud_appkey` 填的是 **离线 Key**，不是 `__UNI__F19B18B`
- 后台应用类型为 **uni-app**
- 删除后台旧 Key 后 **重新生成** 再填入
- Android Studio：**Build → Clean Project** 后重新 `assembleDebug`
- 用解压 APK 的签名 SHA1 与后台对比（须与 `test.jks` 一致）

## 不想配离线 Key 时

可用 HBuilderX **发行 → 制作自定义调试基座（云端）**，由云端写入 AppKey，无需改 `AndroidManifest.xml`。见 [pack-android-ios.md](pack-android-ios.md)。
