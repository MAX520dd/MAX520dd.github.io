---
name: character-persona
description: >-
  分析并撰写语音/对话角色的四要素人设（种族形态、个性、口吻、经历）；须先从官方 B站 Wiki
  #人员档案 抽取至 docs/knowledge/，再蒸馏 personas.json 与角色档案。新建人物、优化人设、
  检查 OOC、扩展干员 Skill 时使用。
---

# 人物性格 Skill（通用）

本 Skill 用于**从源设定提炼可执行的人设**，并同步到 `backend/data/personas.json`。  
任何具体 IP 角色（如斯卡蒂）在 `.cursor/skills/*/characters/` 下写**实例档案**；本 Skill 提供**通用方法论**。

## 何时使用

- 新增一个可对话角色（干员、NPC、if 线变体）
- 修订 `system_prompt` / `few_shot` / `mode_prompts`
- 评估回复是否 OOC
- 要求「再分析一个人物」「写一份人物 skill」

## 四要素（必须全部写清）

| # | 要素 | 核心问题 | 写入 JSON 字段 |
|---|------|----------|----------------|
| 1 | **种族与形态** | 是什么物种？哪条时间线形态？有何可见特征？**明确没有什么** | `race`, `appearance` |
| 2 | **个性** | 对关键人物/阵营的态度？情绪主导？模式切换边界？ | `system_prompt` 性格段、`mode_prompts` |
| 3 | **口吻** | 怎么称呼对方？句长、语气词、修辞习惯？禁止什么口吻？ | `system_prompt` 口吻段、`few_shot` |
| 4 | **经历** | 哪条时间线？记得/忘了什么？执念与恐惧？**不会发生的事** | `system_prompt` 经历段、`mode_few_shot` 触发句 |

四要素互相约束：**形态限制动作描写**，**经历限制话题**，**个性限制情绪组合**，**口吻限制句式**。

## 标准工作流

### A. 分析新角色（产出档案）

**必须先做 Wiki 抽取**：按 [wiki-extraction.md](wiki-extraction.md) 从 B站 Wiki `#人员档案` 录入 `docs/knowledge/<id>-bwiki.md`，再写四要素。世界观仅用 `docs/arknights-world-setting.md`，不替代干员页。

1. **划定实例**：`id`（英文蛇形）、`name`、时间线/皮肤/if 线说明。
2. **官方 Wiki 抽取（P0）**：
   - 抓取基础档案、客观履历、档案资料、语音记录；
   - 写 `docs/knowledge/<id>-bwiki.md` + **证据表**（事实 / Wiki 区块 / 是否进 prompt）；
   - 同页其他时间线内容标为「背景参考」，禁止混入本实例。
3. **填四要素表**：用 [template.md](template.md)；第 1 节必须含「形态禁止」；顶部链回知识库。
4. **派生对话结构**：
   - `emotions`：3~6 个可区分语气标签
   - `modes`：2~4 个**互斥主导情绪**场景（见 [reference.md](reference.md)）
   - `mode_prompts`：每模式「表现 + 本轮禁止」
   - `few_shot` / `mode_few_shot`：每模式至少 2 组，覆盖称呼、句长、典型矛盾
5. **写输出契约**：字数、`<cot>` 格式、`[emotion:]`；旁白**仅**全角括号（…），禁止「」、半角 `()`（与 `persona.py` 的 `normalize_roleplay_brackets` 一致）。
6. **硬边界表**：与易混角色对比（同姓不同线、同世界观不同阵营）。
7. **落盘**（三层）：
   - 知识库 → `docs/knowledge/<id>-bwiki.md`
   - 角色档案 → `.cursor/skills/<pack>/characters/<id>.md`
   - 运行时 → `backend/data/personas.json`（压缩，不贴 Wiki 全文）
8. **自检**：用文末检查表 + [wiki-extraction.md](wiki-extraction.md) §5 证据表。

### B. 从分析到「更多人物 Skill」

每增加一个角色，复制一套实例（不必改本 Skill）：

```
.cursor/skills/<ip-or-project>-persona/
├── SKILL.md                 # 可选：该 IP 共用禁止项、输出契约
└── characters/
    ├── <character-a>.md     # 四要素完整档案
    └── <character-b>.md
```

本仓库示例：

- 通用方法：`.cursor/skills/character-persona/`（本目录）
- 斯卡蒂实例包：`.cursor/skills/arknights-skadi-persona/`

新角色优先写 `characters/<id>.md`，再在实例包 `SKILL.md` 的「角色索引」加一行。

### C. 同步 personas.json

`system_prompt` 建议结构（顺序固定）：

```
【身份/时间线】→【种族】→【外貌+形态禁止】→【性格】→【口吻+称呼】→【经历边界】→【输出格式】
```

`race` / `appearance` 与 `system_prompt` 一致；`description` 一行摘要（给前端列表）。

## 分析提纲（复制使用）

```markdown
## 角色：<name> (`<id>`)

### 1. 种族与形态
- 种族：
- 身份/时间线：
- 外貌要点：
- 形态禁止（硬性）：

### 2. 个性
- 核心：
- 对 <关键对象>：
- 模式表：| mode | 表现 | 禁止 |

### 3. 口吻
- 称呼：
- 句长/语气词/修辞：
- 合格示例 ×2：
- 不合格示例 ×2：

### 4. 经历
- 时间线：
- 关键经历：
- 不会经历的事：

### 5. 硬边界（vs 易混角色）

### 6. JSON 同步清单
- [ ] race / appearance / description
- [ ] system_prompt
- [ ] emotions / modes / mode_labels / mode_prompts
- [ ] few_shot / mode_few_shot
```

## 提交前自检

```
- [ ] 已从 B站 Wiki #人员档案 抽取并写入 docs/knowledge/<id>-bwiki.md
- [ ] 证据表已填；推断与官方原文已区分
- [ ] 未把 Wiki 全文写入 system_prompt；意象可自然口语化
- [ ] 四要素均已填写，且第 1 节含「形态禁止」
- [ ] 口吻含「仅允许的称呼」与禁止称呼
- [ ] 经历含「不会经历的事」
- [ ] modes 两两之间禁止项不矛盾（同一句不触发两模式）
- [ ] few_shot 满足项目 cot / emotion 解析规则
- [ ] 与易混角色硬边界表已写
- [ ] personas.json 已同步
- [ ] 实例包 SKILL.md 角色索引已链知识库
```

## 延伸阅读

- **官方 Wiki 抽取规则**：[wiki-extraction.md](wiki-extraction.md)
- 详细评分 rubric：[reference.md](reference.md)
- 分析源材料步骤：[analysis-guide.md](analysis-guide.md)
- 空白模板：[template.md](template.md)
- 泰拉世界观（非干员档案）：[docs/arknights-world-setting.md](../../../docs/arknights-world-setting.md)
- 斯卡蒂实例：[../arknights-skadi-persona/SKILL.md](../arknights-skadi-persona/SKILL.md)
