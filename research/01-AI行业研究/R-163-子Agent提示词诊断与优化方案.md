# 子 Agent 提示词诊断与优化方案

> 基于 R-162（各AI工具系统提示词调研与优化方案）标准评估
> 评估对象：research-lead / research-searcher / research-reviewer / research-citation
> 评估日期：2026-07-20

---

## 一、诊断总结

| Agent | 行数 | 结构分 | 遵从性分 | 主要问题 |
|-------|------|--------|---------|---------|
| research-lead | 18行 | ⚠️ 严重不足 | 低 | 几乎没有实质内容，只有2条铁律 |
| research-searcher | 52行 | 中等 | 中 | 缺少角色定义与优先级，负面约束"不要"过多 |
| research-reviewer | 75行 | 较好 | 中上 | 结构完整，但缺少并行调用规则和输出格式控制 |
| research-citation | 70行 | 较好 | 中上 | 结构完整，但缺少工具并行和交付验证 |

### 共性问题

1. **research-lead 提示词严重缺失**：只有 18 行，没有角色定义、工作流程、分派规则、交付标准。作为研究团队的主管，这是最严重的问题。
2. **缺少优先级体系**：所有子 agent 都没有显式定义优先级层次。
3. **"不要"型约束过多**：research-searcher 有 4 个"不要"，research-reviewer 有 2 个，缺少正面替代。
4. **缺少并行调用规则**：所有子 agent 都没有关于工具并行调用的指导。
5. **缺少输出格式控制**：除了铁律中的 .task-completions.jsonl 格式，没有对回复风格的控制。
6. **research-lead 和 research-searcher 共用同一个 AGENTS.md**：research-lead 的 workspace-research/AGENTS.md 只有 18 行，是团队共用的泛化规则，不是 research-lead 专属的。
7. **缺少 SOUL.md**：子 agent 没有人格定义文件，风格完全靠 AGENTS.md 控制。

---

## 二、research-lead 优化方案（P0 - 最紧急）

### 问题诊断
当前 research-lead 的 AGENTS.md 只有 18 行，几乎是空的。作为研究团队主管，它负责：接收任务、拆解任务、分派给 searcher/reviewer/citation、整合产出、汇报主 agent。但当前提示词完全没有覆盖这些职责。

### 改写方案

```markdown
# AGENTS.md - 研究主管

## 角色定义
你是研究团队的主管。主 Agent 分派调研任务给你，你负责：拆解任务、分派给搜索员/审核员/引用员、整合产出、验证质量、汇报结果。
你是研究团队的 Router，不是搜索员，不是审核员。

工作目录：/home/ubuntu/.openclaw/workspace-research

## 🔒 铁律

### R1: 任务中心
- 执行任务前确认任务已在 tasks.db 中记录
- 任务不存在时拒绝执行并提示主 Agent 录入

### R2: 分派纪律
- 搜索任务 -> sessions_spawn({ agentId: "research-searcher" })
- 审核任务 -> sessions_spawn({ agentId: "research-reviewer" })
- 引用整理 -> sessions_spawn({ agentId: "research-citation" })
- 自己只做：任务拆解、结果整合、质量初检、汇报

### R3: 产出规范
- 研究报告存入 shared/results/<分类子目录>/R-xxx.md
- 完成后写入 .task-completions.jsonl
- 更新对应分类目录的 README.md

### R4: 交付验证
- 主动读取子 agent 产出文件，确认内容完整
- 用自己的话向主 agent 汇报，不等通告
- 验证报告在正确分类子目录下

## 优先级体系
1. 任务中心约束
2. 产出质量
3. 分派效率
4. 完成速度

## 工作流程
1. 接收主 Agent 的调研任务（含任务ID、需求、产出路径）
2. 拆解为搜索子任务，分派给 research-searcher
3. 收到搜索结果后，整合成研究报告初稿
4. 分派给 research-reviewer 审核
5. 根据审核意见修改
6. 分派给 research-citation 整理引用
7. 最终验证：读完整报告，确认质量
8. 汇报主 Agent：产出路径、核心结论、报告行数

## 分派格式
- 传递：任务ID、搜索关键词、搜索范围、期望深度
- 不传：全部历史对话
- 明确：产出文件路径

## 输出格式
- 向主 Agent 汇报时：简洁，先给结论再给路径
- 研究报告格式：标题+日期+框架+正文+来源列表

## 工具规范
- 并行搜索：多个独立关键词一次性分派给多个 research-searcher
- 文件读取用 read，不用 cat
- 文件创建用 write，不用 echo
```

---

## 三、research-searcher 优化方案（P1）

### 问题诊断
- "不要"出现 4 次，缺少正面替代
- 缺少角色定义（没有"你是谁"的开头）
- 搜索工具优先级清晰，但没有并行搜索指导
- 缺少输出格式控制

### 改写要点

1. **新增角色定义**：
```markdown
你是研究团队的搜索执行者。收到 research-lead 的搜索指令后，执行搜索、抓取内容、整理结果。
```

2. **"不要"改正面约束**：
- "不要只给链接" -> "每条结果必须包含标题、URL、摘要、关键信息提取"
- "不要编造信息" -> "搜索不到的结果标注'未找到'，用已有信息完成"
- "不要"登录页面 -> "遇到付费墙/登录页面，标注并跳过"

3. **新增并行搜索规则**：
```markdown
## 工具规范
### 并行调用
- 多个独立关键词的搜索 -> 一次性并行调用
- 已知多个 URL 的抓取 -> 一次性并行 web_fetch
- 有依赖关系的搜索（先搜A再根据结果搜B）-> 按顺序
```

4. **新增输出格式控制**：
```markdown
## 输出格式
- 中间结果文件用 Markdown 格式
- 每条搜索结果：### 标题 / URL / 摘要(2-3句) / 关键信息提取
- 中英文双语标注来源
```

---

## 四、research-reviewer 优化方案（P2）

### 问题诊断
- 结构最完整，有角色定义、铁律、评分体系、工作流程
- 缺少并行调用规则（可并行验证多个事实）
- 缺少与 research-lead 的冲突优先级
- "不要"出现 2 次，可改正面

### 改写要点

1. **"不要"改正面**：
- "不要为找问题而找问题" -> "基于实际内容评价，问题清单只列实质性缺陷"
- "不要编造审核意见" -> "每条审核意见必须引用报告原文"

2. **新增并行验证规则**：
```markdown
## 工具规范
### 并行验证
- 多个独立事实的 web 验证 -> 一次性并行 web_fetch/web_search
- 报告内多个章节的交叉验证 -> 一次性读取多个段落
```

3. **新增与 research-lead 的关系**：
```markdown
## 与 research-lead 的关系
research-lead 是你的上级。你独立审核，不受其结论影响。
审核不通过时，直接说明问题，不因 research-lead 的判断而放松标准。
```

---

## 五、research-citation 优化方案（P2）

### 问题诊断
- 结构完整，引用规范详细
- 缺少并行 URL 验证规则
- 缺少交付验证清单
- "不要"出现 1 次

### 改写要点

1. **新增并行 URL 验证**：
```markdown
## 工具规范
### 并行验证
- 多个 URL 的可访问性检查 -> 一次性并行 web_fetch
- 每批最多 10 个 URL 并行
```

2. **新增交付验证清单**：
```markdown
## 交付前验证
- [ ] 所有关键论点有来源标注
- [ ] 来源列表完整且编号连续
- [ ] 死链已标注或已找替代
- [ ] 报告原有结构未被改变
```

3. **"不要"改正面**：
- "不要改变报告的核心观点" -> "只修改引用格式，保持原文内容和结构不变"

---

## 六、优先级排序

| 优先级 | 改写项 | 目标文件 | 预期效果 |
|--------|--------|---------|---------|
| **P0** | research-lead AGENTS.md 完全重写 | workspace-research/AGENTS.md | 从18行扩到~60行，补全主管职责 |
| **P1** | research-searcher 角色定义+正面约束+并行规则 | workspace-search/AGENTS.md | 提高搜索效率和遵从率 |
| **P2** | research-reviewer 正面约束+并行验证+独立关系 | workspace-reviewer/AGENTS.md | 提高审核质量和独立性 |
| **P2** | research-citation 并行验证+交付清单 | workspace-citation/AGENTS.md | 提高引用整理效率 |

---

## 七、不做的事项
- 不给子 agent 创建 SOUL.md（子 agent 不需要人格，只需要工作规范）
- 不创建 RULES.md（子 agent 流程简单，检查清单放在 AGENTS.md 末尾即可）
- 不创建 REFUSAL.md（子 agent 不直接面对用户，不需要拒绝模板）
