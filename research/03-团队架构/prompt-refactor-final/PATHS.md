# PATHS.md — 全局路径规范（优化稿）

> 所有路径定义以本文件为唯一真相源；其他文件只引用，不重复定义。
> 只列当前有效路径。已停用的固定团队目录不再作为工作路径。

## 系统级路径

| 名称 | 路径 |
|---|---|
| OpenClaw 全局配置 | `/root/.openclaw/openclaw.json` |
| 主 workspace | `/root/.openclaw/workspace/` |
| 共享目录 | `/root/.openclaw/workspace/shared/` |
| 研究报告目录 | `/root/.openclaw/workspace/shared/results/` |
| 报告过程素材 | `/root/.openclaw/workspace/shared/results/work/` |
| 任务/脚本目录 | `/root/.openclaw/workspace/scripts/` |
| 项目目录 | `/root/.openclaw/workspace/tools/<项目名>/` |
| 提示词评审稿目录 | `/root/dsh-workspace/report/` |

## 研究报告分类目录（2026-08-16 实际目录）

| 编号 | 目录 | 适用内容 |
|---|---|---|
| 01 | `01-AI行业研究` | AI 行业动态、竞品 |
| 02 | `02-AI技术调研` | 技术调研、提示词、框架对比 |
| 03 | `03-团队架构` | 多 agent 架构、流程规范 |
| 04 | `04-投资研究` | 因子、策略、投资分析 |
| 05 | `05-变现与增长` | 变现方案、增长策略 |
| 07 | `07-产品调研` | 产品功能、渠道、Bug |
| 08 | `08-开发实践` | 开发案例、工具分析 |
| 09 | `09-生活杂项` | 生活类杂项 |
| 10 | `10-旅行攻略` | 出行计划 |
| 11 | `11-财务分析` | 财务、账单 |
| 12 | `12-育儿` | 育儿相关 |
| 13 | `13-游戏研究` | 游戏设计、玩法 |
| 14 | `14-个股研报` | 个股研究 |
| 15 | `15-产品方案` | 产品方案 |
| 16 | `16-安全研究` | 安全、运维 |
| 17 | `17-量化投资` | 量化（与 04 重叠，待合并） |
| 18 | `18-智能家居` | HA、家居自动化 |
| 19 | `19-其他` | 未分类 |

> ⚠️ 当前 `shared/results/` 存在重复编号：两个 `05-*`、以及 `17-量化投资` 与 `04-投资研究` 职能重叠。下次整理时建议重命名并以 `README.md` 为准；报告产出前先核对 `shared/results/README.md`。

## 研究报告命名与写入规则

- 命名：`R-xxx.md`（三位数字，如 `R-121.md`），冻结不更新。
- 每个研究任务只产出一份最终报告，放到正式分类目录；多份过程子文件放 `shared/results/work/`。
- 报告写入后必须更新 `shared/results/README.md` 顶部更新日志。

## 开发项目路径

| 文件 | 路径 |
|---|---|
| 项目根目录 | `/root/.openclaw/workspace/tools/<项目名>/` |
| 项目规则文件 | `<项目根目录>/CLAUDE.md` |
| 完成回报 | `/root/.openclaw/workspace/scripts/.task-completions.jsonl` |
| 任务通知队列 | `/root/.openclaw/workspace/scripts/.task-notifications.jsonl` |
| 内部审核 token | `/root/.openclaw/workspace/scripts/.task-center-internal-token` |

## 已归档路径（禁止继续使用）

| 旧路径/旧概念 | 状态 |
|---|---|
| 固定团队 workspace（`workspace-research/`、`workspace-dev/` 等） | 已停用/归档；按需 spawn 继承主 workspace |
| `shared/projects/<项目>/PRODUCT.md` | 废弃；项目文件在项目根目录 |
| dispatch.js cron 调度 | 已停用；主 agent 自行 spawn + 审核 |

## 使用原则

1. 绝对路径优先，跨 agent 引用统一从本文件取。
2. 路径新增/变更只改本文件，其他文件不得重复定义。
3. 项目内部文件在项目根目录操作，不做跨 workspace 路径计算。
4. 报告分类以 `shared/results/README.md` 当前实际目录为准。
