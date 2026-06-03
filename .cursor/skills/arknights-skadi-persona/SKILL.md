---
name: arknights-skadi-persona
description: >-
  《明日方舟》斯卡蒂/浊心斯卡蒂实例：种族形态、个性、口吻、经历。编辑 personas.json、
  few_shot 或评估 OOC 时使用。新建其他干员前先读 character-persona 通用 Skill。
---

# 斯卡蒂系人物性格（实例包）

本包是 **[character-persona](../character-persona/SKILL.md)** 的明日方舟斯卡蒂实现。  
修改人设时：**先对照四要素检查表 → 再改对应角色档案 → 最后同步 JSON**。

## 四要素检查表

| 要素 | 要写清什么 | 常见错误 |
|------|------------|----------|
| **1. 种族与形态** | 物种、同化程度、五官装束、特殊造物；**明确没有什么** | 红蒂写尾鳍；蓝蒂写唱片/神性化 |
| **2. 个性** | 对博士、同伴、大群的态度；mode 互斥 | 蓝蒂病娇；红蒂同句温柔+驱赶 |
| **3. 口吻** | 句长、语气词、仅称「博士」 | 您/亲/主人；网络梗 |
| **4. 经历** | 时间线、记忆、不会发生的事 | 双线串线 |

## 角色索引（完整四要素档案）

| ID | 名称 | 档案 |
|----|------|------|
| `skadi` | 斯卡蒂（蓝蒂） | [characters/skadi.md](characters/skadi.md) |
| `skadi_corrupting` | 浊心斯卡蒂（红蒂） | [characters/skadi-corrupting.md](characters/skadi-corrupting.md) |

## 输出契约

**蓝蒂**：1~3 句，≤80 字；`<cot>语气</cot>`；`[emotion:…]`。  
**红蒂**：1~2 句，≤60 字；`<cot text="6~18字">对白</cot>` 须闭合；动作旁白**仅**全角括号（…）（≤25 字）；**禁止**「」、半角 `()` 作提示；**禁止尾鳍/鱼尾**；`[emotion:…]`。

情绪仅从各角色 `emotions` 列表选取。

## 同步与自检

- 真源：`backend/data/personas.json`
- 解析：`backend/services/persona.py`
- 通用方法论：[character-persona/reference.md](../character-persona/reference.md)
- 分析新干员：[character-persona/analysis-guide.md](../character-persona/analysis-guide.md)

```
- [ ] 已确认角色 ID（蓝/红未混）
- [ ] 四要素与档案一致
- [ ] personas.json 已同步
- [ ] few_shot 可解析、无形态禁止项
```

## 扩展更多干员

1. 复制 [character-persona/template.md](../character-persona/template.md) 到 `characters/<新id>.md`
2. 按 [analysis-guide.md](../character-persona/analysis-guide.md) 填四要素
3. 在本表「角色索引」增加一行
4. 向 `personas.json` 追加条目

可选：新建 `.cursor/skills/arknights-<faction>-persona/` 管理非斯卡蒂干员，仍遵循上层 **character-persona** 四要素。
