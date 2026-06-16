# R-052 Claude Code长时间持续Coding的最佳实践与提示词工程

> 研究日期：2026-04-12 | 分类：AI技术调研 | 复杂度：中等
> 面向场景：用Claude Code重构已有data agent前端项目（接口复用，只重写前端）

---

## 核心发现

### 一、CLAUDE.md的最佳写法和结构

#### 1.1 CLAUDE.md的三层配置体系

Claude Code的配置有**三层级联**机制，每层有不同的作用域和优先级：

| 层级 | 路径 | 作用域 | 典型内容 |
|------|------|--------|----------|
| 全局 | `~/.claude/CLAUDE.md` | 所有项目 | 个人编码风格、通用偏好 |
| 项目根 | `./CLAUDE.md` | 当前项目 | 项目架构、技术栈、API约定 |
| 子目录 | `./src/components/CLAUDE.md` | 特定目录 | 组件规范、命名约定 |

**实战建议**：
- 项目根的CLAUDE.md是**最重要**的配置文件，控制~80%的Claude Code行为
- 子目录CLAUDE.md用于大型项目中不同模块有不同的规范
- 全局CLAUDE.md只放通用偏好，避免和项目配置冲突

#### 1.2 CLAUDE.md推荐结构

基于多个高星GitHub项目和社区经验，推荐的CLAUDE.md结构如下：

```markdown
# 项目名称

## 项目概述
- 项目定位和目标
- 技术栈版本（React 18 + TypeScript 5 + Vite 5 等）

## 架构约定
- 目录结构说明
- 状态管理方案
- 路由结构
- API调用层

## 编码规范
- 组件命名：PascalCase（如 `DataAgentDashboard`）
- 文件命名：kebab-case（如 `agent-list.tsx`）
- TypeScript严格模式
- CSS方案（Tailwind / CSS Modules / styled-components）

## API约定
- 接口基础路径
- 认证方式
- 错误处理规范
- ★ 接口复用约束（见下文详细模板）

## 测试规范
- 测试框架
- 覆盖率要求
- 测试命令

## 禁止事项
- 不要修改的文件/目录
- 不要引入的依赖
- 不要改变的行为
```

#### 1.3 高星CLAUDE.md模板参考

以下GitHub项目提供了高质量的CLAUDE.md配置参考：

| 项目 | Stars | 特点 |
|------|-------|------|
| **everything-claude-code** | 91k+ | 最全面的Claude Code配置集合，含skills/hooks/MCP/commands |
| **claude-code-best-practices** (MuhammadUsmanGM) | 高星 | 社区维护的最佳实践指南，含CLAUDE.md模板和hook脚本 |
| **claude-code-showcase** (ChrisWiles) | 中等 | hooks/skills/agents/commands/GitHub Actions完整示例 |
| **claude-code-templates** (davila7) | 500K+下载 | CLI工具管理Claude Code组件的模板库 |
| **my-claude-code-setup** (centminmod) | 中等 | memory bank文件系统，跨会话保持上下文 |

---

### 二、长会话上下文管理技巧

#### 2.1 上下文漂移（Context Drift）的防护

长时间coding最大的问题是Claude Code会"忘记"早期的约定。以下是社区验证的防护方法：

**① CLAUDE.md作为持久记忆**
- Claude Code每次会话启动都会重新读取CLAUDE.md
- 所有重要约束必须写在CLAUDE.md中，不能只在对话中口头说明
- 社区共识："如果你的约束不在CLAUDE.md里，就等于不存在"

**② .claude/ 目录的深度利用**

```
.claude/
├── CLAUDE.md              ← 项目级指令（可选，也可放根目录）
├── commands/              ← 自定义斜杠命令
│   ├── refactor.md        ← /refactor 命令
│   ├── review.md          ← /review 命令
│   └── test.md            ← /test 命令
├── skills/                ← 技能包
│   ├── frontend/          
│   │   └── SKILL.md       ← 前端开发技能
│   └── api-integration/
│       └── SKILL.md       ← API集成技能
└── settings.json          ← 项目设置（MCP配置等）
```

**③ Memory Bank模式**（centminmod方法）
- 在项目中创建 `memory/` 或 `context/` 目录
- 存放项目状态、已完成任务、待办事项
- CLAUDE.md中引用这些文件来恢复上下文
- 适合跨多天的长周期项目

**④ 自定义命令保持一致性**
- 创建 `/plan` 命令：强制Claude先规划再编码
- 创建 `/check` 命令：检查当前代码是否符合规范
- 创建 `/status` 命令：汇总当前进度

#### 2.2 2000小时实战经验总结

Reddit用户分享了2025年用Claude Code累计2000小时的核心教训：

1. **永远先Plan Mode**：不要直接开始coding，先让Claude分析代码库并制定计划
2. **小步提交**：每完成一个功能就git commit，方便回滚
3. **频繁使用 `/compact`**：当对话变长时压缩上下文，保持响应质量
4. **分阶段工作**：不要试图在一次会话中完成整个重构，按模块/页面拆分
5. **零信任验证**：Claude写的每一行代码都需要人工审查，尤其是API调用
6. **自动格式化Hook要谨慎**：格式化hook可能消耗大量context tokens（报告过3轮用掉160k tokens）

---

### 三、分阶段编码策略（大型前端重构）

#### 3.1 四阶段工作流（官方推荐）

Anthropic官方文档推荐的Claude Code工作流有四个阶段：

```
Phase 1: Explore（探索）
└── Plan Mode → Claude只读不写，分析代码库结构
    命令：claude --print（只输出不执行）

Phase 2: Plan（规划）
└── 制定重构计划，确定模块拆分方案
    输出：写入 docs/refactor-plan.md

Phase 3: Implement（实现）
└── 按模块逐步实现，每次一个独立模块
    使用 subagent 并行开发独立模块

Phase 4: Verify（验证）
└── 运行测试，检查类型，人工review
```

#### 3.2 前端重构的模块拆分策略

针对"接口复用、只重写前端"的场景，推荐以下拆分顺序：

```
Week 1: 基础设施层
├── 项目初始化（Vite + React/Vue + TypeScript）
├── 路由配置
├── API层封装（复用现有接口）
├── 全局状态管理
└── 通用组件库（Button、Table、Modal等）

Week 2: 核心页面层
├── 登录/认证页
├── 首页/Dashboard
├── 数据列表页（带分页、筛选）
└── 数据详情页

Week 3: 功能模块层
├── 图表/可视化组件
├── 表单组件（CRUD）
├── 通知/消息系统
└── 权限控制

Week 4: 打磨与迁移
├── 响应式适配
├── 性能优化
├── E2E测试
└── 灰度发布
```

#### 3.3 Subagent并行开发

Claude Code支持Subagent（子代理）并行工作，特别适合独立模块：

```
# 在项目根目录启动Claude Code后：
# 让Claude用subagent并行处理独立模块

示例指令：
"用plan mode分析这个项目的模块依赖关系，然后为以下三个独立模块分别创建subagent：
1. 认证模块（登录、注册、权限）
2. 数据表格模块（列表、分页、筛选）
3. 图表可视化模块
每个subagent只负责自己的模块，共享API层和通用组件。"
```

**注意事项**：
- Subagent之间不能直接通信，通过共享文件（如API类型定义）协调
- 每个Subagent有独立的context window，需要在CLAUDE.md中给出充分的项目上下文
- 优先处理无依赖的模块，有依赖的后做

---

### 四、针对前端重构的CLAUDE.md模板

#### 4.1 完整示例：Data Agent前端重构项目

以下是专为"接口复用、只重写前端"场景设计的CLAUDE.md模板：

```markdown
# Data Agent 前端重构项目

## 项目概述
本项目是对已有Data Agent系统的前端进行全面重构。
- 后端API已存在且稳定，前端需要重新实现
- 核心原则：**所有API接口必须复用，不修改任何后端代码**
- 新技术栈：React 18 + TypeScript 5 + Vite 5 + Tailwind CSS 3
- 状态管理：Zustand
- 图表库：ECharts 5
- UI组件库：Ant Design 5

## 目录结构约定
```
src/
├── api/              ← API调用层（从旧项目迁移，保持接口不变）
├── components/       ← 通用组件
│   ├── ui/           ← 基础UI组件
│   └── business/     ← 业务组件
├── pages/            ← 页面组件（按路由组织）
│   ├── dashboard/    ← 数据看板
│   ├── agent/        ← Agent管理
│   ├── data/         ← 数据管理
│   └── settings/     ← 系统设置
├── hooks/            ← 自定义Hooks
├── stores/           ← Zustand状态管理
├── types/            ← TypeScript类型定义
├── utils/            ← 工具函数
└── styles/           ← 全局样式
```

## API复用约束（⚠️ 最高优先级）
1. API基础路径：`/api/v1`
2. 认证方式：Bearer Token，存储在localStorage的`access_token`中
3. **绝对禁止**修改任何API请求的URL、参数格式或响应处理逻辑
4. API函数签名必须与旧项目保持一致，便于灰度切换
5. 所有API类型定义从旧项目的Swagger/OpenAPI文档生成
6. API错误统一处理：401跳转登录，403提示权限不足，500全局Toast

## API接口清单
- `GET /api/v1/agents` — 获取Agent列表
- `POST /api/v1/agents` — 创建Agent
- `GET /api/v1/agents/:id` — 获取Agent详情
- `PUT /api/v1/agents/:id` — 更新Agent
- `DELETE /api/v1/agents/:id` — 删除Agent
- `GET /api/v1/agents/:id/executions` — 获取执行历史
- `POST /api/v1/agents/:id/execute` — 触发执行
- `GET /api/v1/data/sources` — 获取数据源列表
- `GET /api/v1/dashboard/stats` — 获取统计数据
- `WebSocket /ws/agents/:id/status` — Agent状态实时推送

## 编码规范
- 组件命名：PascalCase（如 `AgentListTable`）
- 文件命名：kebab-case（如 `agent-list-table.tsx`）
- 每个组件文件不超过300行
- 复杂逻辑抽取为自定义Hook
- 所有API调用使用React Query（TanStack Query）
- 表单使用React Hook Form + Zod验证

## 组件开发规范
1. 每个业务组件必须有对应的`*.types.ts`文件定义props类型
2. 组件必须有默认的空状态和加载状态
3. 列表组件必须支持分页和空数据展示
4. 图表组件必须配置响应式resize
5. 所有用户交互必须有loading状态和error处理

## 样式规范
- 使用Tailwind CSS为主，复杂动画用CSS Modules
- 颜色变量定义在`styles/variables.css`中
- 遵循8px栅格系统
- 暗色模式支持（通过Tailwind的dark:前缀）

## Git规范
- 分支命名：`refactor/模块名-简述`（如 `refactor/dashboard-layout`）
- Commit格式：`refactor(scope): 描述`（如 `refactor(dashboard): 重构数据看板布局`）
- 每个功能模块一个PR

## 禁止事项
- ❌ 不修改任何后端代码或API接口
- ❌ 不引入新的UI组件库（只用Ant Design）
- ❌ 不使用any类型（除非有详细注释说明原因）
- ❌ 不在组件中直接写API调用（通过hooks封装）
- ❌ 不硬编码任何URL或配置值
```

#### 4.2 接口复用约束的高级写法

在CLAUDE.md中描述"接口复用"这种关键约束时，需要注意：

**✅ 正确写法**：
```markdown
## API复用约束
1. 给出具体的API清单（URL、方法、参数）
2. 明确说明哪些接口绝对不能改
3. 给出API调用的示例代码
4. 定义错误处理的统一方式
5. 说明认证和鉴权机制
```

**❌ 错误写法**：
```markdown
## API
- 复用现有API
- 不要修改后端
- 参考旧项目的API调用方式
```

**关键原则**：
- Claude Code是代码级AI，它需要**具体的代码示例**，不是笼统的描述
- 越具体的约束越不容易被违反
- 包含"禁止事项"清单比包含"应该做"更有效

#### 4.3 阶段性提示词模板

**阶段1 - 项目初始化**：
```
请帮我初始化一个新的React + TypeScript + Vite项目，用于重构Data Agent的前端。
请按照CLAUDE.md中的目录结构创建所有目录和基础文件。
先创建package.json和tsconfig.json，等确认后再继续。
不要安装任何npm包，只创建项目结构。
```

**阶段2 - API层迁移**：
```
现在我们需要把旧项目的API层迁移到新项目。
旧项目的API代码在 ../old-project/src/api/ 目录下。
请逐个文件读取旧API代码，按新项目的规范重写。
注意：
1. 保持API函数签名完全一致
2. 使用axios替代旧项目中的fetch
3. 添加完整的TypeScript类型定义
4. 统一错误处理逻辑
每次完成一个文件的迁移后暂停等我确认。
```

**阶段3 - 页面实现**：
```
现在实现Dashboard页面。请先进入plan mode分析：
1. 这个页面需要展示哪些数据
2. 需要调用哪些API
3. 页面布局结构
4. 需要哪些子组件

确认计划后再开始编码。按以下顺序实现：
1. 页面骨架（布局）
2. 数据获取（API调用）
3. 子组件实现
4. 样式和交互
5. 响应式适配
```

---

### 五、MCP配置与工具链集成

#### 5.1 前端开发推荐MCP配置

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-filesystem", "/path/to/project"]
    }
  }
}
```

**推荐的MCP Server**：
| MCP Server | 用途 | 是否必需 |
|------------|------|----------|
| **Playwright MCP** | 浏览器自动化，验证UI效果 | 强烈推荐 |
| **GitHub MCP** | 创建PR、管理Issues | 推荐 |
| **Filesystem MCP** | 文件系统操作 | 推荐 |
| **Apidog MCP** | API文档和Mock数据 | 可选 |
| **Figma MCP** | 设计稿转代码 | 可选 |

#### 5.2 Hooks配置建议

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'About to modify file'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command", 
            "command": "npx prettier --write $FILE_PATH"
          }
        ]
      }
    ]
  }
}
```

**⚠️ 重要警告**：自动格式化hooks可能消耗大量context tokens（有报告称3轮就用掉160k tokens）。建议：
- 简单项目可以用自动格式化
- 大型项目考虑手动格式化，或在会话之间运行
- 或者只在git commit时触发格式化

---

### 六、Dashboard/数据可视化前端项目的特殊注意点

#### 6.1 数据可视化项目的CLAUDE.md补充

```markdown
## 数据可视化规范
1. 图表组件统一使用ECharts，通过useECharts hook封装
2. 每个图表必须配置：
   - loading状态（骨架屏）
   - 空数据状态
   - 错误状态
   - 响应式resize（使用ResizeObserver）
3. 大数据量图表（>1000条数据）必须开启数据采样或虚拟滚动
4. 图表颜色使用统一配色方案，定义在 styles/chart-theme.ts
5. WebSocket实时数据更新：
   - 使用自定义hook useWebSocket
   - 断线自动重连（指数退避）
   - 数据更新使用requestAnimationFrame节流
```

#### 6.2 前端重构的常见陷阱

| 陷阱 | 解决方案 |
|------|----------|
| Claude可能"发明"不存在的API | 在CLAUDE.md中列出完整API清单 |
| 组件间状态传递混乱 | 用Zustand全局状态，避免多层props传递 |
| 样式不一致 | 定义统一的设计tokens，在CLAUDE.md中引用 |
| 过度工程化 | 在CLAUDE.md中明确"保持简单"的原则 |
| 一次性生成太多代码 | 要求"每次只做一个功能，完成后暂停确认" |
| 忘记之前讨论的约定 | 每次重要决定都更新CLAUDE.md |

---

### 七、Claude Code与同类工具对比（前端重构场景）

| 特性 | Claude Code | Cursor | GitHub Copilot |
|------|------------|--------|----------------|
| 全项目理解 | ★★★★★ | ★★★★ | ★★★ |
| CLAUDE.md/规则 | ★★★★★ | ★★★ | ★★ |
| Plan Mode | ★★★★★ | ★★★★ | ★★ |
| Subagent | ★★★★★ | ★★ | ★ |
| 终端集成 | ★★★★★ | ★★★★ | ★★★ |
| 前端专化 | ★★★★ | ★★★★★ | ★★★★ |
| 价格 | API按量 | $20/月 | $10-39/月 |

**结论**：对于大型前端重构项目，Claude Code的CLAUDE.md规则系统和Subagent并行能力使其成为最佳选择。Cursor在单文件编辑体验上更好，但不适合跨多天的持续重构项目。

---

## 实践建议（按优先级排序）

### 必做项（P0）
1. **编写完整的CLAUDE.md**：包含项目概述、架构、API清单、编码规范、禁止事项
2. **始终使用Plan Mode启动**：先让Claude分析再编码，避免方向错误
3. **小步提交**：每完成一个模块就commit，方便回滚
4. **API清单要具体**：列出每个接口的URL、方法、参数，不要只说"复用现有API"

### 推荐项（P1）
5. 配置Playwright MCP用于UI验证
6. 创建自定义命令（/plan、/review、/test）
7. 设置.gitignore中的CLAUDE.md跟踪
8. 使用subagent并行开发独立模块

### 可选项（P2）
9. 配置自动格式化hook（注意token消耗）
10. 使用Figma MCP从设计稿转代码
11. 设置memory bank系统跨会话保持上下文

---

## 来源列表

### 英文来源
1. [Claude Code官方文档 - Best Practices](https://code.claude.com/docs/en/best-practices) — Anthropic官方最佳实践
2. [Claude Code官方文档 - .claude Directory](https://code.claude.com/docs/en/claude-directory) — .claude目录结构官方说明
3. [Claude Code官方文档 - Memory](https://code.claude.com/docs/en/memory) — 记忆系统说明
4. [Claude Code官方文档 - Common Workflows](https://code.claude.com/docs/en/common-workflows) — 常见工作流
5. [50 Claude Code Tips - Builder.io](https://www.builder.io/blog/claude-code-tips-best-practices) — 50条实用技巧
6. [Claude Code Best Practices (GitHub Pages)](https://rosmur.github.io/claudecode-best-practices/) — 社区综合最佳实践
7. [Best Practices: Lessons From Real Projects](https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/) — 真实项目经验
8. [claude-code-best-practices (GitHub)](https://github.com/MuhammadUsmanGM/claude-code-best-practices) — 社区维护指南
9. [claude-code-showcase (GitHub)](https://github.com/ChrisWiles/claude-code-showcase) — 配置示例集
10. [claude-code-templates (GitHub)](https://github.com/davila7/claude-code-templates) — 模板库
11. [my-claude-code-setup (GitHub)](https://github.com/centminmod/my-claude-code-setup) — Memory Bank方案
12. [HuggingFace: 10 Essential Claude Code Best Practices](https://discuss.huggingface.co/t/10-essential-claude-code-best-practices-you-need-to-know/174731) — 84条最佳实践
13. [Reddit: 2000 Hours Coding With Claude Code](https://www.reddit.com/r/ClaudeCode/comments/1q7nhn6/) — 2000小时实战经验
14. [Reddit: How I Structure Claude Code Projects](https://www.reddit.com/r/Anthropic/comments/1ru4rs8/) — 项目结构经验
15. [Reddit: Frontend Dev Setup for Claude Code](https://www.reddit.com/r/ClaudeCode/comments/1mrvfmf/) — 前端开发配置
16. [Claude Code Subagents Guide (Medium)](https://medium.com/@richardhightower/claude-code-subagents-and-main-agent-coordination-a4f88ae8f46c) — Subagent协调
17. [The .claude Folder Guide (TowardsAI)](https://pub.towardsai.net/the-claude-folder-is-important-and-youre-likely-ignoring-it-33fc97f6d9fa) — .claude文件夹详解
18. [Frontend Development Best Practices Skill (MCP Market)](https://mcpmarket.com/tools/skills/frontend-development-best-practices) — 前端技能包
19. [Claude Code Skills Structure (mikhail.io)](https://mikhail.io/2025/10/claude-code-skills/) — Skills内部机制
20. [Vibehackers: Claude Code Hooks & Subagents](https://vibehackers.io/blog/claude-code-hooks-guide) — Hooks和高级功能

### 中文来源
21. [Claude Code官方最佳实践指南 - EasyClaude](https://easyclaude.com/post/claude-code-official-best-practices) — 官方指南中文解读
22. [Claude Code最佳实践的8条黄金法则 - 腾讯云](https://cloud.tencent.com/developer/article/2617720) — CTO分享实战法则
23. [Claude Code最佳实践完全指南 - 知识铺](https://index.zshipu.com/ai/post/20251007/) — 26个实战技巧
24. [AI驱动前端重构 - 阿里云开发者](https://developer.aliyun.com/article/1675950) — 10天3000+行组件重构实战
25. [Claude Code深度指南 - 幂简集成](https://www.explinks.com/blog/yt-claude-code-setup-guide-ai-dev-efficiency/) — 重构和Git效率提升

---

## 知识缺口

1. **Vue.js + Claude Code的专门经验**：大部分高质量来源基于React，Vue项目的Claude Code经验较少
2. **Claude Code的Context Window实际使用极限**：缺乏关于单个会话最长可持续多长时间的定量数据
3. **Subagent的具体性能基准**：并行subagent在大型前端项目中的实际效率提升缺乏量化数据
4. **企业级前端项目的Claude Code配置**：大部分案例来自个人开发者/小团队，大型企业项目的配置经验较少
