# 表情包资源

| 目录 | 角色 | persona_id |
|------|------|------------|
| `skd/` | 斯卡蒂（蓝蒂） | `skadi` |
| `zhuoxinskd/` | 浊心斯卡蒂 | `skadi_corrupting` |

将 jpg/png 放入对应文件夹后，在 `backend/data/game_catalog.json` 的 `sticker_packs` 里为条目增加 `"image": "文件名.jpg"`，并同步 `uniapp/utils/sticker-images.js`（可选，服务端已返回 `/static/biaoqingbao/...` 路径）。

开发时源文件也可放在 `uniapp/biaoqingbao/`，复制到本目录：`cp -R ../biaoqingbao/* ./`
