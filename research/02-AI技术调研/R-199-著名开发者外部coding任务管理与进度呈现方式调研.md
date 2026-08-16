# 著名开发者外部 Coding 任务管理与进度呈现方式调研

> **报告编号**: R-199  
> **调研日期**: 2026-08-11  
> **调研范围**: 知名开发者/Indie Hacker 的任务管理工具、工作流、进度可视化方式  
> **特别关注**: 外部 coding 场景（客户项目、交付要求、进度可见性）

---

## 目录

1. [调研背景与方法论](#1-调研背景与方法论)
2. [Pieter Levels (@levelsio) — 极简透明派](#2-pieter-levels-levelsio--极简透明派)
3. [Marc Lou — 速度至上派](#3-marc-lou--速度至上派)
4. [DHH (David Heinemeier Hansson) — Shape Up 方法论](#4-dhh-david-heinemeier-hansson--shape-up-方法论)
5. [ThePrimeagen — 环境效率派](#5-theprimeagen--环境效率派)
6. [Kent C. Dodds — 开源自动化派](#6-kent-c-dodds--开源自动化派)
7. [TODO.md / Markdown 驱动的任务管理趋势](#7-todomd--markdown-驱动的任务管理趋势)
8. [工具对比表](#8-工具对比表)
9. [任务/进度呈现方式分类](#9-任务进度呈现方式分类)
10. [外部 Coding 场景的特殊需求与实践](#10-外部-coding-场景的特殊需求与实践)
11. [对 OpenClaw Dashboard 的启发建议](#11-对-openclaw-dashboard-的启发建议)
12. [参考来源](#12-参考来源)

---

## 1. 调研背景与方法论

### 1.1 调研目标

理解知名开发者如何在实际工作中进行任务管理、进度追踪和可视化呈现，重点关注：
- 他们使用的具体工具（Notion、Linear、GitHub Issues、TODO.md 等）
- 进度呈现方式（看板、时间线、仪表盘、社交媒体）
- 任务拆解粒度和优先级管理策略
- 外部 coding（客户项目）场景的特殊需求

### 1.2 关于"龙虾"的说明

任务中提到的"龙虾（Lobster / 芋头）"经广泛搜索后，在开发者社区中未找到以"龙虾"为昵称的、以详细记录开发过程著称的特定开发者 blogger。搜索结果中的"龙虾"绝大多数指向 OpenClaw（其中文社区昵称为"龙虾"）。因此，本报告将调研重心调整为全球范围内最具代表性的知名独立开发者/Indie Hacker，覆盖不同风格和场景。

### 1.3 调研方法

- 搜索引擎多轮检索（英文为主）
- 直接抓取开发者博客原文、采访稿、工具对比文章
- 交叉验证多个来源的信息一致性
- 所有引用均来自真实搜索结果

---

## 2. Pieter Levels (@levelsio) — 极简透明派

### 2.1 基本信息

| 项目 | 详情 |
|------|------|
| **身份** | 独立开发者 / 数字游民 / 创业者 |
| **代表产品** | Nomad List、Remote OK、Photo AI、GoFuckingDoIt |
| **年收入** | 约 $2.7M+/年（2024-2025 数据），月收入峰值超 $300K |
| **团队规模** | 一人（仅雇佣兼职服务器安全和社区审核人员） |
| **推特粉丝** | 600K+ |

### 2.2 任务管理工具：几乎不用

Levels 的任务管理方式可能是所有知名开发者中最"反工具"的：

- **不用 Git**：历史部署方式是 Sublime Text 写代码 → 本地测试 → SFTP 直接上传。后续版本管理靠备份软件的无限历史记录和编辑器内 undo（来源：levels.io/deviance）
- **不用项目管理软件**：不用 Jira、不用 Notion、不用 Trello、不用 Linear
- **不用框架**：vanilla PHP + jQuery，RemoteOK.io 整个网站是一个 PHP 单文件
- **编辑器**：Sublime Text 3（后来可能切换到其他工具，但始终极简）

他的"项目管理"实际上是通过以下方式完成的：
- **一个文件夹结构** 搞定一切：`/_assets`（设计稿）、`/public/assets/`（前端资源）、`/app/`（前后端代码）、`/lib/`（第三方库）、`/workers/`（定时任务）、`/logs/`（日志）、`/data/`（JSON 文件代替数据库）
- **直接写代码** 而不是写任务清单

### 2.3 进度呈现方式：极致的"Build in Public"

Levels 的进度呈现不是内部看板，而是**面向公众的实时仪表盘和社交媒体**：

#### (1) Open Startup™ 实时仪表盘
- Nomad List 在 nomadlist.com/open 上**实时公开所有收入数据和用户指标**
- 包括：MRR（月经常性收入）、用户数、流量、API 调用量
- 这是他"开放创业"理念的直接体现

#### (2) levels.io/projects — 项目成功率追踪
- 他做了一个动态页面 `levels.io/projects`，实时追踪自己所有项目的"成功率"
- 公开承认：70+ 项目中只有 4-5 个赚钱，命中率约 5-8%
- 这种"失败率可视化"在开发者中极为罕见

#### (3) Twitter 生物实时更新
- MRR 数据直接写在 Twitter 生物中
- 每达到里程碑立即发推："Revenue update for fly.pieter.com after 13 days: Hit $67,000 MRR (+$10K from yday)"

#### (4) 博客长文里程碑总结
- 重要节点会写详细博客（如 "Normalization of non-deviance" 总结了从 0 到 $1M/年的历程）

### 2.4 优先级管理

Levels 的优先级管理极其直觉化：
- **解决自己的问题**（"scratching your own itch"）：Nomad List 源于自己想知道哪个城市适合数字游民
- **快速验证**：12 startups in 12 months 挑战，每个项目最短数天内上线
- **失败就放弃**：不沉溺于沉没成本，95% 的项目失败了但不妨碍成功的那几个
- **用户反馈驱动**：上线后根据真实用户反馈快速迭代

### 2.5 关键启发

> **核心哲学**：工具越少越好，速度就是一切，透明度是最好的营销。

---

## 3. Marc Lou — 速度至上派

### 3.1 基本信息

| 项目 | 详情 |
|------|------|
| **身份** | 独立开发者 / Indie Hacker |
| **代表产品** | ShipFast（Next.js boilerplate）、CodeFast、IndiePage |
| **年收入** | $50K+/月（2024 数据），年收入超百万美元 |
| **产品数量** | 2年内发布了 16+ 个产品 |
| **特色** | Product Hunt "Maker of the Year" |

### 3.2 任务管理工具：Notion + 极简清单

Marc Lou 的任务管理体现了"快速发布"哲学：

- **Notion 作为核心工作台**：使用 Notion 管理产品规划、任务清单和日常待办
- **Indie Hacker Startup OS 模板模式**：在 Notion 中构建包含产品规划、收入追踪、待办事项的一体化工作空间
- **每日计划器（Daily Planner）**：在 Notion 中搭建每日任务看板，按优先级排列
- **产品模板化**：ShipFast 本身就是一套 Next.js 启动模板，本质上是将"快速启动"流程化为产品

### 3.3 进度呈现方式：社交媒体 + 公开收入

- **LinkedIn/Twitter 公开收入**："I made $63,247 in September 2024" 这类帖子
- **Product Hunt 发布**：每个新产品都通过 Product Hunt 发布，作为里程碑节点
- **YouTube/Instagram 视频**：通过视频内容分享开发过程和成果
- **ShipFast 本身的产品页面**：作为"成果展示"的窗口

### 3.4 优先级管理

Marc Lou 的策略可以总结为 **"Ship Fast Playbook"**：

1. **模板复用**：所有新产品都基于 ShipFast boilerplate，省去重复配置
2. **时间盒（Time Boxing）**：限定每个产品的开发时间，到时间就发布
3. **收入优先**：能快速产生收入的功能优先开发
4. **营销驱动开发**：先把着陆页和营销做好，再完善产品
5. **同时运营多个产品组合**：不把鸡蛋放在一个篮子里

### 3.5 关键启发

> **核心哲学**：模板化 + 批量发布 + 营销优先。任务是"发多少个产品"，而不是"完善一个产品"。

---

## 4. DHH (David Heinemeier Hansson) — Shape Up 方法论

### 4.1 基本信息

| 项目 | 详情 |
|------|------|
| **身份** | Basecamp/37signals 联合创始人 & CTO；Ruby on Rails 创造者 |
| **代表产品** | Basecamp、HEY；Ruby on Rails 框架 |
| **团队规模** | ~50 人（Basecamp） |
| **著作** | REWORK、It Doesn't Have to Be Crazy at Work、REMOTE、Shape Up |
| **特色** | 反 VC、反加班、反复杂工具；"Calm Company" 理念 |

### 4.2 任务管理工具：Basecamp + Shape Up 方法论

DHH 的任务管理分为两个层面：个人工作方式和团队方法论。

#### 个人层面：极简到极致

来源：Lifehacker 采访 "I'm David Heinemeier Hansson, Basecamp CTO, and This Is How I Work"

- **不用待办清单**："I don't, really. I try not to have a backlog."
- **Inbox Zero**：邮件即时处理，大部分回复"No"
- **工具选择**：
  - TextMate（代码编辑器，从 2003 年用到现在）
  - iA Writer（散文写作）
  - OS X/iOS Notes（灵感记录）
- **工作时间**：每天 4-5 小时真正专注的工作时间
- **核心原则**："Saying no" — 拒绝几乎一切，专注于极少数真正重要的事

#### 团队层面：Shape Up 方法论

来源：basecamp.com/shapeup（开源书籍）

Shape Up 是 Basecamp 内部产品开发方法，核心要素：

**（1）六周周期（Six-Week Cycles）**
- 所有工作以六周为一个周期
- 六周足够长：可以从头到尾构建有意义的东西
- 六周足够短：每个人从一开始就能感受到截止日期的压力
- 大部分新功能在一个六周周期内完成并发布

**（2）Shaping（塑造工作）**
- 在将工作交给团队之前，由高级小组先"塑造"
- 定义解决方案的关键要素，在合适的抽象层级：
  - 足够具体：团队知道要做什么
  - 足够抽象：团队有空间自己解决有趣的细节
- 核心概念是 **Appetite（胃口）**：不问"这要花多久"，而问"我们愿意花多少时间"

**（3）Betting（下注）**
- 每个周期开始时，决策者"下注"选择哪些被塑造的项目
- 默认规则：如果一个项目超时，**不会自动延期**（"circuit breaker"熔断机制）
- 这迫使人们在塑造阶段就解决大部分不确定性

**（4）团队自主**
- 小型集成团队（2-3 人，含设计和编程）
- 团队自己定义任务、调整范围
- 构建"垂直切片"：一次构建一个端到端的有意义功能
- 没有每日站会，没有细粒度的时间追踪

### 4.3 进度呈现方式

- **Basecamp 内置工具**：To-do 列表、消息板、里程碑、文件分享
- **六周周期的自然节奏**：不需要复杂的中期汇报，周期结束即交付
- **Shape Up 书籍本身**：将内部方法论完整公开，作为"最好的文档"
- **HE 27signals 博客**：分享决策和思考过程

### 4.4 优先级管理

DHH 的优先级管理是所有调研对象中最"哲学化"的：

1. **Appetite-based prioritization**：基于"愿意投入多少"而非"需要多久"
2. **熔断机制**：项目超时即终止，不追加投资
3. **风险优先排序**：先解决最不确定的部分，集成验证
4. **少即是多**：一个六周周期只做 1-2 个大项目，做透
5. **拒绝的力量**：DHH 个人说"No"的次数远多于"Yes"

### 4.5 关键启发

> **核心哲学**：固定时间，可变范围。在时间盒内做最有价值的工作，超时就停。团队自主 > 微观管理。

---

## 5. ThePrimeagen — 环境效率派

### 5.1 基本信息

| 项目 | 详情 |
|------|------|
| **身份** | Netflix 高级软件工程师 / Twitch 主播 |
| **代表作品** | Developer Productivity 课程；Neovim 生态贡献 |
| **粉丝** | YouTube/Twitch 数百万订阅 |
| **特色** | 以极致的开发环境配置和工作流优化著称 |

### 5.2 任务管理工具：环境即工具

ThePrimeagen 不推崇任何传统 PM 工具，他的"任务管理"是通过**极致的环境优化**来实现的：

来源：Sourcegraph "Dev Tool Time" 采访；linkarzu.com 博客复现

- **Neovim**：核心编辑器，高度自定义配置
- **Tmux**：终端多路复用器，在一个屏幕内管理多个会话/窗口/面板
- **i3/Yabai（窗口管理器）**：键盘驱动的窗口布局，零鼠标操作
- **Dotfiles 管理**：跨机器同步所有配置，新机器几分钟内恢复完整环境
- **认知开销最小化**：所有操作通过键盘快捷键完成，减少上下文切换

### 5.3 进度呈现方式

- **Twitch 直播**：实时展示编码过程，进度本身就是内容
- **YouTube 视频**：按主题/里程碑发布，如"Developer Productivity"课程
- **GitHub 仓库**：开源配置和工具
- **社交媒体短帖**：在 Twitter/Instagram 分享见解

### 5.4 优先级管理

- **认知开销优先**：减少"找文件、切换窗口、记命令"的心智负担
- **工具链自动化**：让重复性工作消失，专注于真正的编程问题
- **流状态（Flow State）保护**：环境配置的目标是"让你忘记工具的存在"

### 5.5 关键启发

> **核心哲学**：最好的任务管理是让你不需要任务管理——环境如此流畅，以至于工作本身就是进度。

---

## 6. Kent C. Dodds — 开源自动化派

### 6.1 基本信息

| 项目 | 详情 |
|------|------|
| **身份** | JavaScript 教育者 / 开源贡献者 / 前 React 核心贡献者 |
| **代表作品** | Epic React、Testing JavaScript、React Testing Library |
| **特色** | 以高质量教学内容和系统化的开发方法论著称 |

### 6.2 任务管理工具：GitHub 生态 + 自动化

来源：kentcdodds.com 博客；GitHub AMA

- **GitHub Issues**：核心任务追踪工具，用于开源项目的 bug 追踪、功能请求、讨论
- **GitHub Projects**：看板视图管理 issue 和 PR
- **自动化优先**：一切可自动化的都自动化（CI/CD、测试、发布）
- **Colocation 原则**：相关的东西放在一起——测试和代码在一起、文档和代码在一起

### 6.3 进度呈现方式

- **GitHub 里程碑和 Release**：每个版本有清晰的里程碑和 changelog
- **博客文章**：kentcdodds.com 上的技术深度文章，记录决策和思考
- **AMA（Ask Me Anything）**：GitHub Issues 中的 AMA 让任何人提问
- **YouTube/课程平台**：教学内容本身就是进度的体现
- **Twitter/X 分享**：日常更新和见解

### 6.4 优先级管理

- **自动化消除重复**："automating repetitive workflows lets me keep my brain focused on the task at hand"（来源：kentcdodds.com/blog/automation）
- **影响力优先**：选择能帮助最多人的工作（教学 > 个人项目）
- **Colocation 减少决策**：不需要思考"这个放哪里"，因为相关的东西总在一起

### 6.5 关键启发

> **核心哲学**：自动化一切重复工作，让人类只做需要创造力的事。GitHub Issues 就是最好的 PM 工具——如果你的工作本来就在 GitHub 上。

---

## 7. TODO.md / Markdown 驱动的任务管理趋势

### 7.1 现象描述

一个值得关注的趋势是：越来越多开发者回归**纯文本/Markdown 驱动**的任务管理方式，特别是在 AI 编程时代。

### 7.2 代表项目与实践

| 项目/实践 | 描述 | 来源 |
|-----------|------|------|
| **TODO.md 规范** | 标准化的 Markdown TODO 文件格式，支持多项目任务管理 | github.com/todo-md/todo-md |
| **Tasks.md** | 自托管的 Markdown 文件任务管理系统，有现代看板界面 | github.com/BaldissaraMatheus/Tasks.md |
| **taskmd** | AI 时代本地优先的 Markdown 任务系统，专为 AI 编程 Agent 设计 | Medium: taskmd |
| **Git-based task management** | 将 Markdown 任务文件纳入 Git 版本控制，实现变更追踪和协作 | pankajpipada.com 博客 |

### 7.3 为什么 Markdown 任务管理在回归

1. **AI Agent 友好**：纯文本格式天然适合 AI 读写，不需要 API 集成
2. **零依赖**：任何编辑器都能打开
3. **版本控制**：与 Git 天然集成，任务变更有历史记录
4. **极简**：不会陷入"配置工具"的陷阱
5. **可组合**：可以和 CI/CD、静态站点生成器等工具链无缝组合

### 7.4 典型 TODO.md 结构

```markdown
# Project Name

## In Progress
- [ ] Implement user authentication
- [ ] Design dashboard layout

## Next
- [ ] Add payment integration
- [ ] Write API documentation

## Later
- [ ] Mobile app version
- [ ] Multi-language support

## Done
- [x] Set up project repository
- [x] Create initial wireframes
```

---

## 8. 工具对比表

### 8.1 开发者使用的工具概览

| 开发者 | 核心任务管理 | 进度呈现 | 优先级策略 | 外部可见度 |
|--------|-------------|---------|-----------|-----------|
| **Pieter Levels** | 无（直接写代码）；文件夹结构 | Open Startup 实时仪表盘；Twitter MRR；levels.io/projects | 直觉+用户反馈 | ★★★★★ |
| **Marc Lou** | Notion（日常计划+产品规划） | 公开收入帖；Product Hunt 发布 | 收入优先+时间盒 | ★★★★★ |
| **DHH** | Basecamp（团队）；无（个人） | Shape Up 六周周期；博客 | Appetite-based+熔断 | ★★★★☆ |
| **ThePrimeagen** | Neovim+Tmux 环境 | Twitch 直播；YouTube 视频 | 认知开销最小化 | ★★★★☆ |
| **Kent C. Dodds** | GitHub Issues+Projects | GitHub Milestones；博客 | 影响力+自动化 | ★★★★☆ |

### 8.2 主流 PM 工具对比（适用于独立开发者/小团队）

| 工具 | 价格 | 核心优势 | 主要劣势 | 适用场景 |
|------|------|---------|---------|---------|
| **Notion** | 免费(个人)/$10/月(团队) | 无限灵活；文档+任务一体；丰富模板 | 速度慢；容易过度配置 | 规划期；非技术任务混合 |
| **Linear** | 免费(250 issues)/$8/月 | 极速键盘操作；Sprint/周期；开发者优先 | 仅适合软件开发；非灵活 | 快速迭代的小型开发团队 |
| **GitHub Projects** | 免费 | 与代码库零切换；Issue/PR 自动关联 | 报告弱；无 burndown 图 | 开源项目；代码在 GitHub 的团队 |
| **TODO.md** | 免费 | AI 友好；Git 原生；零依赖 | 无 UI；纯手动维护 | AI Agent 工作流；极简主义者 |
| **Trello** | 免费/$10/月 | 直观的看板；上手零成本 | 功能有限 | 简单任务可视化 |
| **Todoist** | 免费/$3/月 | 极简清单；自然语言输入 | 不适合复杂项目管理 | 个人日常任务 |
| **Basecamp** | $99/月(不限用户) | 内置完整协作；To-do+消息+日程 | 价格高；功能固定 | 客户协作；中型团队 |
| **ClickUp** | 免费/$5/月 | 功能全面；时间追踪+目标管理 | 学习曲线陡 | 需要一站式解决方案的团队 |

### 8.3 功能矩阵

| 功能 | Notion | Linear | GitHub Projects | TODO.md | Basecamp |
|------|--------|--------|----------------|---------|----------|
| 看板视图 | ✅ | ✅ | ✅ | ❌(纯文本) | ✅ |
| 时间线/甘特图 | ✅ | ✅ | ❌ | ❌ | ✅ |
| Sprint/周期 | ❌ | ✅ | ✅(迭代) | ❌ | ✅(六周) |
| 文档/Wiki | ✅ | ❌ | ❌(但有Wiki) | ❌ | ✅ |
| 代码集成 | ❌ | ✅ | ✅(原生) | ✅(Git) | ❌ |
| API/Webhook | ✅ | ✅ | ✅ | ✅(文件) | ✅ |
| 自动化 | ✅ | ✅ | ✅ | ❌ | ✅ |
| 客户门户 | ❌ | ❌ | ❌(公开可见) | ❌ | ✅ |
| AI 友好度 | △ | △ | △ | ✅ | ❌ |
| 客户可见进度 | △(可分享) | ❌ | △(公开仓库) | △(可公开) | ✅ |

---

## 9. 任务/进度呈现方式分类

根据调研，知名开发者的进度呈现方式可归纳为以下五大类：

### 9.1 实时仪表盘型（Dashboard）

**代表人物**: Pieter Levels

- 实时展示收入、用户、流量的公开仪表盘
- 项目成功率追踪页面
- 特点：**数据驱动、完全透明、实时更新**
- 适用场景：Build in Public、营销引流、自我激励

### 9.2 周期里程碑型（Cycle / Milestone）

**代表人物**: DHH / Basecamp

- 固定时间周期（六周），周期结束时交付
- 不需要频繁的进度汇报，周期即节奏
- 特点：**低频高质、减少汇报开销**
- 适用场景：团队协作、产品开发

### 9.3 社交媒体直播型（Social Streaming）

**代表人物**: Pieter Levels、Marc Lou、ThePrimeagen

- 通过 Twitter/LinkedIn 公开收入和里程碑
- 通过 Twitch/YouTube 实时展示编码过程
- 特点：**进度即内容、透明即营销**
- 适用场景：个人品牌建设、社区运营

### 9.4 代码库嵌入型（Code-Native）

**代表人物**: Kent C. Dodds、开源社区

- GitHub Issues + Projects + Milestones
- PR 描述中包含进度和决策
- Release Notes 作为里程碑记录
- 特点：**零上下文切换、开发流程原生**
- 适用场景：开源项目、技术团队

### 9.5 文件清单型（Flat File）

**代表人物**: TODO.md 社区、AI Agent 时代开发者

- 纯 Markdown 文件记录任务清单
- 三列模式：Now / Next / Later
- 特点：**极简、AI 友好、Git 原生**
- 适用场景：AI Agent 工作流、个人项目

---

## 10. 外部 Coding 场景的特殊需求与实践

### 10.1 外部 Coding 与个人产品的核心差异

| 维度 | 个人产品 | 外部 Coding（客户项目） |
|------|---------|----------------------|
| **目标** | 自己觉得有用/赚钱 | 满足客户需求 |
| **截止日期** | 自己定 | 客户/合同约定 |
| **需求变更** | 自己说了算 | 需要变更管理流程 |
| **进度可见性** | 可选公开 | **必须向客户可见** |
| **交付标准** | 自己定义 | 合同/SOW 定义 |
| **付款** | 用户付费 | 里程碑付款 |

### 10.2 外部 Coding 的最佳实践（来自调研综合）

#### (1) 里程碑交付（Milestone-Based Delivery）
- 将项目拆分为 3-5 个里程碑
- 每个里程碑有明确的交付物和验收标准
- 里程碑结束触发付款（来源：usmannadeem.com；asrify.com）

#### (2) 客户可见的进度追踪
- **客户门户**：Plutio 等工具提供客户门户，客户可以实时查看项目状态、任务进度和里程碑完成情况
- **Staging 环境**：为客户创建可访问的预览环境，比截图和报告更有说服力
- **定期更新**：每周一次进度更新，而不是等客户来问

#### (3) 需求变更管理
- 使用公开路线图（如 IndieRoadmaps、Planet Roadmap）让客户知道哪些功能在计划中
- 变更请求通过 Issue/Ticket 系统追踪，而非口头沟通

#### (4) 进度追踪的关键指标
- 里程碑完成率
- 任务完成速度（velocity）
- 预算消耗 vs 计划
- 风险项数量

### 10.3 外部 Coding 推荐工具栈

| 需求 | 推荐工具 | 理由 |
|------|---------|------|
| 客户可见的项目管理 | Basecamp / Plutio | 内置客户门户，权限可控 |
| 开发任务追踪 | Linear / GitHub Projects | 开发者友好，效率高 |
| 文档和知识库 | Notion | 灵活，可分享给客户 |
| 部署预览 | Vercel Preview / Netlify Deploy Previews | 每个 PR 自动生成预览链接 |
| 进度汇报 | 自动化 Dashboard | 减少手动写报告的时间 |
| 合同和发票 | Stripe Invoicing / Bonsai | 里程碑付款管理 |

---

## 11. 对 OpenClaw Dashboard 的启发建议

基于以上调研，对 OpenClaw Dashboard 的任务管理和进度呈现提出以下建议：

### 11.1 核心理念：多层级进度可见性

借鉴 levelsio 的实时仪表盘和 Basecamp 的 Shape Up，OpenClaw Dashboard 应该支持**不同层级的进度呈现**：

| 层级 | 面向 | 呈现内容 | 更新频率 |
|------|------|---------|---------|
| L1: 实时状态 | 自己/团队 | 当前任务、正在运行的 Agent、阻塞项 | 实时 |
| L2: 里程碑视图 | 客户/利益相关者 | 里程碑完成度、预计交付日期 | 每周/每里程碑 |
| L3: 社交化展示 | 公众/社区 | 项目概览、成功率、成果展示 | 按需 |

### 11.2 具体功能建议

#### 建议 1：集成 TODO.md / Markdown 任务文件解析

**灵感来源**：TODO.md 社区趋势 + AI Agent 友好

- Dashboard 自动解析工作空间中的 TODO.md / TASKS.md 文件
- 渲染为可视化看板（Now / Next / Later 三列）
- AI Agent 可以直接读写 Markdown 文件，Dashboard 自动同步
- **这比让 AI 通过 API 操作 Notion/Linear 简单得多，也更可靠**

#### 建议 2：实时 Agent 运行状态面板

**灵感来源**：levelsio 的 Open Startup 实时仪表盘

- 显示当前活跃的 Agent 数量和状态
- 每个 Agent 正在做什么任务
- 任务耗时、Token 消耗、完成率
- 类似 levelsio 的 nomadlist.com/open 的风格——简洁的数字+图表

#### 建议 3：里程碑交付追踪

**灵感来源**：Basecamp Shape Up + 外部 coding 最佳实践

- 每个项目可定义 3-5 个里程碑
- 每个里程碑有：标题、描述、验收标准、截止日期、状态
- 里程碑进度条：基于子任务完成百分比
- 可生成**客户友好的里程碑报告**（PDF/网页链接）

#### 建议 4：项目成功率/投资组合视图

**灵感来源**：levelsio 的 levels.io/projects 页面

- 所有项目的概览面板
- 标记每个项目状态：活跃/搁置/失败/成功
- 显示"命中率"——多少比例的项目达成了预期目标
- 鼓励"快速失败"的文化

#### 建议 5：时间周期（Cycle）视图

**灵感来源**：Linear Cycles + Basecamp 六周周期

- 支持按周/双周/自定义周期组织任务
- 周期结束时，未完成任务自动滚入下一周期
- 周期回顾：本期完成了什么、放弃了什么、学到了什么

#### 建议 6：Git-Native 进度追踪

**灵感来源**：Kent C. Dodds 的 GitHub 工作流 + TODO.md 趋势

- Dashboard 与 Git 深度集成
- Commit 消息、PR 标题自动关联到任务
- 代码变更可视化为进度（"这个任务有 15 个 commit，3 个已合并的 PR"）
- Release Notes 自动生成

#### 建议 7：社交化进度分享

**灵感来源**：levelsio 和 Marc Lou 的 Build in Public

- 一键生成"本周进展"摘要
- 可分享的公开 Dashboard 链接（可选范围）
- 集成社交媒体发布（"完成了第 3 个里程碑 🎉"）
- 项目完成时的自动庆祝动画/通知

#### 建议 8：认知开销最小化设计

**灵感来源**：ThePrimeagen 的环境优化哲学

- Dashboard 操作全程支持键盘快捷键
- 任务创建/状态变更/视图切换无需鼠标
- "少于 5 分钟/天"原则：维护 Dashboard 的时间不应超过 5 分钟
- 自动化一切：任务状态变更由代码提交/PR/Agent 行为自动触发

### 11.3 Dashboard 信息架构建议

```
OpenClaw Dashboard
├── 🏠 Overview（总览）
│   ├── 活跃 Agent 数量和状态
│   ├── 今日完成的任务
│   ├── 当前里程碑进度
│   └── 收入/产出指标（可选）
├── 📋 Tasks（任务）
│   ├── Now / Next / Later 看板
│   ├── 按 Agent 分组视图
│   └── 按 Milestone 分组视图
├── 🎯 Milestones（里程碑）
│   ├── 当前周期的里程碑
│   ├── 历史里程碑完成记录
│   └── 客户可见的报告生成
├── 📊 Analytics（分析）
│   ├── 项目成功率
│   ├── Agent 效率统计
│   ├── 周期回顾报告
│   └── 时间/Token 消耗趋势
├── 📁 Projects（项目组合）
│   ├── 所有项目列表和状态
│   ├── 项目健康度评分
│   └── 快速切换/搜索
└── 🔗 Integrations（集成）
    ├── Git 仓库关联
    ├── CI/CD 状态
    └── 外部工具同步（可选）
```

### 11.4 设计原则总结

| 原则 | 灵感来源 | 含义 |
|------|---------|------|
| **Markdown-First** | TODO.md 社区 | 所有数据以 Markdown 文件为 source of truth |
| **Git-Native** | Kent C. Dodds | 进度追踪与代码变更深度绑定 |
| **Real-Time Transparent** | levelsio | 核心指标实时可见，不需要手动更新 |
| **Cycle-Based** | Basecamp / Linear | 以固定周期为节奏，避免无限待办 |
| **Customer-Visible** | 外部 coding 最佳实践 | 一键生成客户友好的进度报告 |
| **Minimal Overhead** | ThePrimeagen | 维护 Dashboard 本身不应成为工作 |
| **AI-Agent Friendly** | TODO.md + taskmd 趋势 | AI 可以直接读写任务文件，无需复杂 API |

---

## 12. 参考来源

### 直接来源（已抓取/阅读）

1. **levels.io/how-i-build-my-minimum-viable-products** — Levels 的 MVP 开发流程详解（编辑器、技术栈、文件夹结构、部署方式）
2. **levels.io/deviance** — "Normalization of non-deviance"，Levels 回顾从 0 到 $1M/年的方法论
3. **basecamp.com/shapeup/0.3-chapter-01** — Shape Up 书籍引言，六周周期方法论
4. **lifehacker.com "I'm DHH, Basecamp CTO, and This Is How I Work"** — DHH 个人工作方式详解
5. **blog.vibecoder.me "Notion vs Linear vs GitHub Projects for Solo Builders"** — 三大工具详细对比
6. **learn.builtthisweek.com "Best PM Tools for Solo Developers in 2025"** — 10 大工具排名和对比表
7. **sourcegraph.com "Dev Tool Time with ThePrimeagen"** — ThePrimeagen 的环境优化理念
8. **linkarzu.com "How I replicated ThePrimeagen's developer workflow"** — Primeagen 工作流复现
9. **kentcdodds.com/blog/automation** — Kent C. Dodds 的自动化哲学
10. **github.com/todo-md/todo-md** — TODO.md 规范
11. **github.com/BaldissaraMatheus/Tasks.md** — 自托管 Markdown 任务管理

### 间接来源（搜索结果摘要）

12. **x.com/levelsio/status/968219339588493312** — Nomad List 成为 Open Startup™ 的公告
13. **x.com/levelsio/status/2064018530966684022** — levels.io/projects 项目成功率追踪页面上线
14. **x.com/levelsio/status/1897784027186446820** — 收入更新推文示例
15. **x.com/levelsio/status/1457315274466594817** — "70+ 项目只有 4 个赚钱"的坦白
16. **indiehackers.com "How Marc Lou makes $50k+ every month"** — Marc Lou 的收入和工作方式
17. **blog.startupstash.com "The Marc Lou Playbook: 15 Ship Fast Truths"** — Marc Lou 的方法论总结
18. **starterstory.com "How Pieter Levels Makes $3.2M/Year"** — Levels 的收入构成分析
19. **softwaregrowth.io "How Pieter Levels grew Nomad List to $3M ARR"** — Nomad List 增长案例
20. **reddit.com/r/indiehackers "Project Management tools for Indie Hackers"** — 社区讨论汇总
21. **reddit.com/r/webdev "Freelancers and solo devs, how are you keeping track"** — 自由职业者工具讨论
22. **plutio.com "How to Deliver Freelance Projects on Time (2026)"** — 里程碑交付实践
23. **usmannadeem.com "Freelance Web Developer PM: How to Handle Large Projects"** — 大型项目里程碑管理
24. **pankajpipada.com "Refining the Flow: Streamlined Markdown/Git-Based Task Management"** — Git + Markdown 任务管理
25. **Medium: taskmd "Task management for the AI era"** — AI 时代的 Markdown 任务管理

---

## 附录 A：调研对象速查卡

```
┌─────────────────┬──────────────┬───────────────┬────────────────────┐
│ 开发者          │ 核心工具      │ 呈现方式       │ 关键词              │
├─────────────────┼──────────────┼───────────────┼────────────────────┤
│ Pieter Levels   │ 无/直接编码   │ 实时仪表盘     │ Build in Public    │
│                 │              │ Twitter MRR   │ Open Startup       │
├─────────────────┼──────────────┼───────────────┼────────────────────┤
│ Marc Lou        │ Notion       │ 社交媒体收入帖 │ Ship Fast          │
│                 │              │ Product Hunt  │ 模板化             │
├─────────────────┼──────────────┼───────────────┼────────────────────┤
│ DHH             │ Basecamp     │ 六周周期交付   │ Shape Up           │
│                 │ 个人: 无     │ 博客+书籍      │ Calm Company       │
├─────────────────┼──────────────┼───────────────┼────────────────────┤
│ ThePrimeagen    │ Neovim+Tmux  │ Twitch 直播   │ Developer Prod.    │
│                 │              │ YouTube 视频  │ 环境优化           │
├─────────────────┼──────────────┼───────────────┼────────────────────┤
│ Kent C. Dodds   │ GitHub       │ Milestones    │ Automation         │
│                 │ Issues/Proj  │ 博客+课程     │ Colocation         │
└─────────────────┴──────────────┴───────────────┴────────────────────┘
```

## 附录 B：推荐阅读清单

1. **《Shape Up》** by Ryan Singer (free online at basecamp.com/shapeup) — Basecamp 团队的产品开发方法
2. **《MAKE》** by Pieter Levels (readmake.com) — Levels 的创业方法论
3. **《REWORK》** by Jason Fried & DHH — 反传统商业智慧
4. **levels.io/how-i-build-my-minimum-viable-products** — MVP 极简开发实战
5. **blog.vibecoder.me Notion vs Linear vs GitHub** — 工具选择决策指南

---

*报告完成。如需进一步深挖某位开发者的具体实践或某个工具的详细使用方式，请告知。*
