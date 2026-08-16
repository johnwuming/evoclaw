# Evoclaw 文件系统规范 v2

> 规范版本：v2
> 发布日期：2026-04-05
> 状态：生效中

---

## 核心原则

1. **本地即仓库**：本地文件系统结构 = GitHub 仓库结构，无二次映射
2. **单出口**：每个团队的交付物只有一个写入位置，路径透明无歧义
3. **极简层级**：目录层级最多 2 层（不含 root），能平铺绝不嵌套

---

## 目录结构

### 本地（`~/.openclaw/`）

```
~/.openclaw/
├── workspace/                      # main agent
│   ├── AGENTS.md                   # ⚙️ 系统配置（不参与同步）
│   ├── SOUL.md / IDENTITY.md / USER.md / TOOLS.md / HEARTBEAT.md / BOOTSTRAP.md
│   ├── memory/                     # main agent 记忆
│   ├── shared/results/             # 📤 研究报告（R-xxx.md）
│   └── main-out/                   # main agent 非配置产出
│
├── workspace-research/             # 研究团队
│   └── research/                   # 研究过程文件（plan.json 等内部文件）
│
├── workspace-dev/                  # 开发团队
│   ├── <project>/                  # 开发项目（每个项目一个目录）
│   │   └── PRODUCT.md              # 项目唯一真相源
│   └── shared/                     # dev 内部共享
│
├── evolving-claw-repo/             # GitHub 仓库（本地 clone，与上方结构 1:1）
│   ├── research/                   # 📤 研究报告
│   │   └── *.md                    # R-xxx.md，全部平铺，无 reports/plans 子分类
│   ├── dev/                        # 开发交付物
│   │   └── <project>/              # 与 workspace-dev/ <project>/ 同名
│   │       └── PRODUCT.md
│   ├── main/                       # main agent 产出
│   │   └── *.md                    # main-out/ 下所有文件（不含系统配置）
│   └── infra/scripts/              # 自动化脚本
│
└── extensions/                     # 插件（不参与同步）
```

### 仓库（`evolving-claw-repo/`）

```
evolving-claw-repo/
├── research/           # R-xxx.md 全部平铺，不再分 reports/plans
│   └── R-001.md ~ R-999.md
├── dev/               # 开发项目，与 workspace-dev/ 同名
│   └── <project>/
│       └── PRODUCT.md
├── main/              # main agent 产出
│   └── *.md
├── infra/scripts/     # auto-sync.sh 等
└── README.md          # 本文件
```

> **注意**：`workspace/` 下的 AGENTS.md、SOUL.md、IDENTITY.md、USER.md、TOOLS.md、HEARTBEAT.md、BOOTSTRAP.md、memory/ 不参与同步，仅本地使用。

---

## 各目录职责

| 目录 | 写入者 | 内容 | 同步方向 |
|------|--------|------|----------|
| `workspace/shared/results/` | 研究主管 | R-xxx.md 研究报告 | → `research/` |
| `workspace/main-out/` | main agent | 分析/方案文档 | → `main/` |
| `workspace-dev/<project>/` | 开发主管 | PRODUCT.md 等 | → `dev/<project>/` |
| `workspace-research/research/` | 研究团队 | plan.json 等过程文件 | → `research/internal/` |

---

## 命名规范

### 研究报告
```
R-xxx-short-title.md
```
- xxx：三位数字，从 001 起递增，**不复用**
- short-title：kebab-case，英文，≤5 词
- 示例：`R-001-research-team-config.md`

### 开发项目
```
<project-name>/
└── PRODUCT.md
```
- 项目目录：kebab-case
- 主文件：`PRODUCT.md`（唯一真相源，活文档）
- 辅助文件：与 PRODUCT.md 同目录，如 `feature-list.json`、`progress.md`

### main agent 产出
```
main-out/<descriptive-name>.md
```
- 目录固定 `main-out/`
- 文件名自描述，kebab-case
- 示例：`main-out/issue-channel-bug.md`、`main-out/system-analysis.md`

### infra 脚本
```
infra/scripts/<purpose>.sh
```
- 示例：`infra/scripts/auto-sync.sh`

---

## 文件协同流程

```
研究团队  ──→  shared/results/R-xxx.md  ──→  research/
    │                                        │
    │                                        ↓
    │                                   dev/ 可引用
    │                                   （通过文件名 R-xxx.md）
    │
开发团队  ──→  workspace-dev/<proj>/PRODUCT.md  ──→  dev/<proj>/
    │
main agent  ──→  main-out/*.md  ──→  main/
```

**跨团队引用规则**：
- dev 引用研究结论 → 使用 `R-xxx.md` 文件名即可，路径统一为 `../research/R-xxx.md`（相对仓库根）
- main 引用研究和开发交付物 → 同上

---

## 自动同步映射规则

### 简化后的 auto-sync.sh 逻辑

| 本地源路径 | 仓库目标路径 | 说明 |
|-----------|-------------|------|
| `workspace/shared/results/R-*.md` | `research/R-*.md` | 全量同步，不分类 |
| `workspace/main-out/*.md` | `main/*.md` | main agent 非配置产出 |
| `workspace-dev/<project>/*` | `dev/<project>/*` | 开发项目整体同步 |
| `workspace-research/research/*` | `research/internal/*` | 研究过程文件 |

**分类逻辑废除**：不再按文件名关键词区分 reports/plans，全部平铺到 `research/`。

### 目录冲突解决

| 问题 | 现状 | 规范 |
|------|------|------|
| `workspace-dev/projects/` 不存在 | auto-sync.sh 监控空目录 | 改为监控 `workspace-dev/` 根目录，映射规则按子目录 |
| `research/reports/` vs `research/plans/` | 两层子目录 | 废除 plans/，reports/ 改名为 research/，平铺 |
| `main/analysis/` / `config/` / `plans/` | 三层子目录 | 废除子类，改为平铺 `main/*.md` |
| `archive/` | 目录不存在 | 废除，不设归档目录 |

### 同步触发条件

- 文件后缀：`.md`、`.json`、`.sh`
- 排除：所有以 `AGENTS.md` `SOUL.md` `IDENTITY.md` `USER.md` `TOOLS.md` `HEARTBEAT.md` `BOOTSTRAP.md` 命名的文件（系统配置不参与同步）
- 触发后：自动 commit，message 格式 `auto: YYYY-MM-DD HH:MM`

---

## 迁移清单（一次性）

- [x] 合并后的 62 个文件已映射到 `shared/results/R-xxx.md`（见 FILE-LAYOUT.md v1 合并表）
- [ ] `workspace/main-out/` 目录创建，原 `workspace/*.md` 非配置产出移入
- [ ] `workspace-dev/` 根目录下建立第一个 `<project>/` 示例（待开发团队填充）
- [ ] auto-sync.sh 更新：删除 keyword 分类逻辑，改为直接 1:1 映射
- [ ] 仓库端：`research/reports/` + `research/plans/` 合并为 `research/`，旧文件迁移
- [ ] 仓库端：`main/analysis/` + `main/config/` + `main/plans/` 合并为 `main/`，旧文件迁移

---

## 附录：旧 → 新路径对照

| 旧路径 | 新路径 |
|--------|--------|
| `research/reports/*.md` | `research/*.md` |
| `research/plans/*.md` | `research/*.md`（合并后） |
| `main/analysis/*.md` | `main/*.md` |
| `main/config/*.md` | `main/*.md` |
| `main/plans/*.md` | `main/*.md` |
| `workspace/merged/` | 废除，内容已合并入 `shared/results/` |
| `workspace/archive/` | 废除，不设归档 |
