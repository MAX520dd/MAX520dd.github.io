---
name: arknights-skadi-persona
description: >-
  《明日方舟》斯卡蒂/浊心斯卡蒂实例。新建或修订人设须先从 B站 Wiki #人员档案 抽取至
  docs/knowledge/，再蒸馏四要素与 personas.json。编辑 few_shot 或评估 OOC 时使用。
---

# 斯卡蒂系人物性格（实例包）

本包是 **[character-persona](../character-persona/SKILL.md)** 的明日方舟斯卡蒂实现。  
修改人设时：**先按 [wiki-extraction.md](../character-persona/wiki-extraction.md) 更新知识库 → 四要素档案 → `personas.json`**（禁止跳过 Wiki 直接改 prompt）。

## 四要素检查表

| 要素 | 要写清什么 | 常见错误 |
|------|------------|----------|
| **1. 种族与形态** | 物种、同化程度、五官装束、特殊造物；**明确没有什么** | 红蒂写尾鳍；蓝蒂写唱片/神性化 |
| **2. 个性** | 对博士、同伴、大群的态度；mode 互斥 | 蓝蒂病娇；红蒂同句温柔+驱赶 |
| **3. 口吻** | 句长、语气词、仅称「博士」 | 您/亲/主人；网络梗 |
| **4. 经历** | 时间线、记忆、不会发生的事 | 双线串线 |

## 角色索引（完整四要素档案）

| ID | 名称 | 档案 | 官方知识库 |
|----|------|------|------------|
| `skadi` | 斯卡蒂（蓝蒂） | [characters/skadi.md](characters/skadi.md) | [docs/knowledge/skadi-bwiki.md](../../../docs/knowledge/skadi-bwiki.md)（[B站 Wiki](https://wiki.biligame.com/arknights/%E6%96%AF%E5%8D%A1%E8%92%82#%E4%BA%BA%E5%91%98%E6%A1%A3%E6%A1%88)） |
| `skadi_corrupting` | 浊心斯卡蒂（红蒂） | [characters/skadi-corrupting.md](characters/skadi-corrupting.md) | [docs/knowledge/skadi-corrupting-bwiki.md](../../../docs/knowledge/skadi-corrupting-bwiki.md)（[B站 Wiki](https://wiki.biligame.com/arknights/%E6%B5%8A%E5%BF%83%E6%96%AF%E5%8D%A1%E8%92%82#%E4%BA%BA%E5%91%98%E6%A1%A3%E6%A1%88)） |

## 输出契约

**蓝蒂**：1~3 句，≤80 字；`<cot text="语气">对白</cot>`；`[emotion:…]`。  
**蓝蒂情绪锚**：`cold` ↔ 距离感、灾祸、独行；`vulnerable`/`gentle` ↔ 担心同伴、保护博士、干燥的好梦。禁止血亲/同化台词。  
**红蒂**：1~2 句，≤60 字；`<cot text="6~18字">对白</cot>` 须闭合；动作旁白**仅**全角括号（…）（≤25 字）；**禁止**「」、半角 `()` 作提示；**禁止尾鳍/鱼尾**；`[emotion:…]`。  
**红蒂情绪锚**：`gentle`/`possessive` ↔ 血亲、故乡、陪伴；`plead`/`sad` ↔ 官方失败语音「快从我身边逃走吧」。同句禁止混用。

## 蓝蒂官方设定要点（Wiki 录入摘要）

- 赏金猎人，13 年经验，阿戈尔；专精剑术（海）与潜水；非感染者。
- 关键词：潮湿→干燥、离群、怕牵连他人、巨剑独行、幽灵鲨、歌谱/哼歌。
- 维护：先读 [skadi-bwiki.md](../../../docs/knowledge/skadi-bwiki.md) → `skadi.md` → `personas.json`。

情绪仅从各角色 `emotions` 列表选取。

## 浊心官方设定要点（Wiki 录入摘要）

- 专精：歌唱（海洋）、同化；非感染者；源石技艺适应性差。
- 人设关键词：熟悉又陌生的访客、等了太久、箱中过去碎片、最后的朋友、干燥、远海之歌。
- 背景勿串：同页主线档案（凯尔希劝当干员、盐风城简报）是**主线斯卡蒂**语境，浊心日常对白不照搬。
- 维护知识库：改人设前先读 [skadi-corrupting-bwiki.md](../../../docs/knowledge/skadi-corrupting-bwiki.md)，再改 `skadi-corrupting.md` 与 `personas.json`。

## 同步与自检

- 真源：`backend/data/personas.json`
- 解析：`backend/services/persona.py`
- **泰拉世界观（校对用，勿每轮背诵）**：[docs/arknights-world-setting.md](../../../docs/arknights-world-setting.md)
- 通用方法论：[character-persona/reference.md](../character-persona/reference.md)
- 分析新干员：[character-persona/analysis-guide.md](../character-persona/analysis-guide.md)

```
- [ ] 已从 B站 Wiki 更新 docs/knowledge/<id>-bwiki.md
- [ ] 已确认角色 ID（蓝/红未混）；同页其他时间线未混入
- [ ] 四要素与知识库、personas.json 一致
- [ ] system_prompt 无 Wiki 长文/科普腔
- [ ] few_shot 可解析、无形态禁止项
```

## 扩展更多干员

1. 打开 B站 Wiki 干员页 `#人员档案`，按 [wiki-extraction.md](../character-persona/wiki-extraction.md) 写 `docs/knowledge/<新id>-bwiki.md`
2. 复制 [template.md](../character-persona/template.md) 到 `characters/<新id>.md`，填四要素 + 证据表
3. 在本表「角色索引」增加一行（档案 + 知识库 + Wiki URL）
4. 向 `personas.json` 追加条目（蒸馏，不贴 Wiki 全文）

可选：新建 `.cursor/skills/arknights-<faction>-persona/` 管理非斯卡蒂干员，仍须遵循 Wiki 抽取规则。
