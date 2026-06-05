# 角色档案目录

每个文件对应 `backend/data/personas.json` 中的一个 `id`，结构遵循 [character-persona/template.md](../../character-persona/template.md)。

| 文件 | id |
|------|-----|
| [skadi.md](skadi.md) | `skadi` |
| [skadi-corrupting.md](skadi-corrupting.md) | `skadi_corrupting` |

**知识库**（官方档案摘录，非每轮注入）：

| 文件 | 来源 |
|------|------|
| [docs/knowledge/skadi-bwiki.md](../../../../docs/knowledge/skadi-bwiki.md) | [B站 Wiki 斯卡蒂](https://wiki.biligame.com/arknights/%E6%96%AF%E5%8D%A1%E8%92%82) |
| [docs/knowledge/skadi-corrupting-bwiki.md](../../../../docs/knowledge/skadi-corrupting-bwiki.md) | [B站 Wiki 浊心斯卡蒂](https://wiki.biligame.com/arknights/%E6%B5%8A%E5%BF%83%E6%96%AF%E5%8D%A1%E8%92%82) |

新增角色：复制 `template.md` → 本目录 `<id>.md` → 更新上级 [SKILL.md](../SKILL.md) 索引 → 写入 `personas.json`。
