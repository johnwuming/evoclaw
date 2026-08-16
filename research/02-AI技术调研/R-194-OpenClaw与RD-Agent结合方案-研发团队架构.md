# OpenClaw 与微软 RD-Agent 结合方案：多 Agent 研发团队架构设计

> **报告编号**: R-194  
> **类别**: AI 技术调研  
> **日期**: 2026-08-10  
> **状态**: 完稿  

---

## 目录

1. [调研背景与目标](#1-调研背景与目标)
2. [RD-Agent 架构深度剖析](#2-rd-agent-架构深度剖析)
3. [OpenClaw 编排能力概览](#3-openclaw-编排能力概览)
4. [三种结合方案设计](#4-三种结合方案设计)
5. [数据流设计](#5-数据流设计)
6. [部署架构方案](#6-部署架构方案)
7. [实施路径与里程碑](#7-实施路径与里程碑)
8. [风险评估与应对](#8-风险评估与应对)
9. [总结与建议](#9-总结与建议)

---

## 1. 调研背景与目标

### 1.1 现状分析

**OpenClaw 现状：**
OpenClaw 是一个多 Agent 编排平台，已具备成熟的会话管理、Cron 调度、任务中心 Dashboard 和 ACP（Agent Communication Protocol）协议支持。当前已部署 6 个 Agent 角色：

- **main**（小朱桑 🦞）：秘书 Agent，负责日常交互和任务分发，工作区 `/root/.openclaw/workspace`
- **research-lead**（研究主管）：研究 Agent，负责深度调研任务编排，工作区 `/root/.openclaw/workspace-research`
- **research-searcher**（研究搜索员）：搜索专家，执行资料检索子任务
- **research-reviewer**（研究审核员）：审核专家，执行报告质量审核
- **research-citation**（研究引用员）：引用专家，执行引用规范检查
- **quant-compute**（量化员）：量化计算 Agent，手动执行因子研究和回测，使用 deepseek-v4-flash 作为主力模型

OpenClaw 配置文件为 `/root/.openclaw/openclaw.json`，网关运行在端口 12145。任务中心是一个独立的 Node.js 服务（`http://127.0.0.1:8055/api/tasks`），提供 REST API 进行任务编排。已配置的通信渠道包括 lightclawbot、QQ Bot 和微信（openclaw-weixin）。通过 Zerotier 连接群晖 NAS（`10.12.192.241`），SSH 通道连接本地 HP 工作站作为计算节点。子 Agent 最大并发 8 个，深度 4 层，超时 2400 秒。

**微软 RD-Agent 现状：**
RD-Agent（github.com/microsoft/RD-Agent）是微软开源的自动化研发框架，核心思想是构建"数据驱动的 R&D 自动化"系统。其核心循环为：

```
LLM 提出假设 → 生成实验代码 → 执行验证 → 获取反馈 → 迭代进化
```

RD-Agent 在 MLE-bench 上排名第一，是当前最强的机器学习工程 Agent。其量化金融场景（RD-Agent(Q)）是首个数据中心的量化多 Agent 框架，在真实股票市场中以低于 $10 的成本实现约 2× 的 ARR，同时使用少于 70% 的因子。该成果已发表于 NeurIPS 2025。

### 1.2 结合动机

当前的痛点十分明确：

1. **quant-compute 是单 Agent、手动驱动**：每次因子研究和回测都需要人工介入，缺乏自动化迭代能力
2. **RD-Agent 有自动循环但缺少编排层**：RD-Agent 擅长研发执行，但缺少任务调度、多角色协作、外部通知等编排能力
3. **两者互补性极强**：OpenClaw 的编排层 + RD-Agent 的研发执行层 = 完整的自动化量化研发体系

### 1.3 调研目标

本报告旨在：
- 深入剖析 RD-Agent 的技术架构，理解其核心组件和扩展机制
- 设计 2-3 种结合方案，对比优缺点和实现难度
- 给出完整的数据流设计、部署方案和实施路径
- 提供 MVP（最小可行方案）到完全融合的渐进式路线图

---

## 2. RD-Agent 架构深度剖析

### 2.1 顶层架构

RD-Agent 的代码结构清晰地分为以下几个层级：

```
rdagent/
├── app/              # 应用入口层（CLI 命令、场景配置）
│   ├── cli.py        # Typer CLI 统一入口
│   ├── qlib_rd_loop/ # Qlib 量化场景配置
│   ├── finetune/     # LLM 微调场景
│   ├── kaggle/       # Kaggle 竞赛场景
│   └── data_science/ # 数据科学场景
├── core/             # 核心框架层
│   ├── evolving_framework.py  # 进化框架抽象
│   ├── evolving_agent.py      # 进化 Agent
│   ├── experiment.py          # 实验抽象
│   ├── proposal.py            # 假设提案
│   ├── developer.py           # 开发者抽象
│   ├── evaluation.py          # 评估器
│   ├── scenario.py            # 场景抽象
│   └── knowledge_base.py      # 知识库
├── components/       # 可复用组件层
│   ├── coder/        # 代码生成组件
│   ├── runner/       # 执行运行组件
│   ├── proposal/     # 假设生成组件
│   ├── workflow/     # 工作流（RDLoop）
│   ├── loader/       # 加载器
│   └── knowledge_management/
├── scenarios/        # 场景实现层
│   ├── qlib/         # Qlib 量化场景
│   │   ├── proposal/      # 因子/模型假设生成
│   │   ├── developer/     # 因子/模型代码实现
│   │   ├── experiment/    # 实验定义与工作区
│   │   └── factor_experiment_loader/  # 因子加载
│   ├── finetune/     # 微调场景
│   ├── kaggle/       # Kaggle 场景
│   └── shared/       # 共享工具
├── oai/              # LLM 后端层
│   ├── llm_conf.py   # LLM 配置
│   ├── llm_utils.py  # LLM 调用工具
│   └── backend/      # 后端实现（LiteLLM 等）
├── log/              # 日志与 UI 层
│   ├── server/       # Flask 后端 API
│   ├── ui/           # Streamlit UI + Web UI
│   └── storage.py    # 日志存储
└── utils/            # 工具层
    ├── env.py        # 环境管理（Docker/Conda）
    ├── workflow/     # 循环工作流引擎
    └── qlib.py       # Qlib 工具函数
```

### 2.2 核心循环引擎：RDLoop

RD-Agent 的核心工作流由 `RDLoop` 类（`rdagent/components/workflow/rd_loop.py`）驱动，它继承自 `LoopBase`，采用元类 `LoopMeta` 自动发现和排序步骤。

**RDLoop 的标准步骤链：**

```
direct_exp_gen → coding → running → feedback → record
```

每个步骤的职责：

| 步骤 | 方法 | 输入 | 输出 | 职责 |
|------|------|------|------|------|
| `direct_exp_gen` | 异步 | 上一轮 trace | `{propose, exp_gen}` | 生成假设 + 转化为实验任务 |
| `coding` | 同步 | 实验任务 | 编码后的 workspace | CoSTEER 系统生成代码 |
| `running` | 同步 | 编码后的 workspace | 回测结果 | 在 Docker/Conda 中执行 |
| `feedback` | 同步 | 回测结果 | `HypothesisFeedback` | 评估结果、生成反馈 |
| `record` | 同步 | feedback + exp | 更新 trace | 记录历史、推进进化 |

**LoopBase 引擎的核心特性：**

1. **Session 持久化**：每个步骤完成后自动 pickle dump 到 `__session__/` 目录，支持断点续跑
2. **并行执行**：通过 `step_semaphore` 配置支持多 loop 并行（`RD_AGENT_SETTINGS.step_semaphore`）
3. **错误处理**：`skip_loop_error` 定义可跳过的异常类型，`withdraw_loop_error` 定义回退到上一轮的异常类型
4. **定时终止**：支持 `all_duration` 参数设置总运行时长
5. **子进程隔离**：`force_subproc=True` 时通过 `ProcessPoolExecutor` 在子进程中执行步骤

### 2.3 进化框架抽象

`evolving_framework.py` 定义了进化的核心抽象：

- **`EvolvableSubjects`**：被进化的对象（因子、模型等），支持 `clone()` 深拷贝
- **`EvoStep`**：一次进化步骤，包含 `evolvable_subjects`、`queried_knowledge`、`feedback`
- **`EvolvingStrategy`**：进化策略抽象，`evolve_iter` 方法产出迭代器实现逐步进化
- **`RAGStrategy`**：检索增强生成策略，管理知识库的查询和更新

### 2.4 Qlib 量化场景详解

#### 2.4.1 场景配置系统

Qlib 场景的配置位于 `rdagent/app/qlib_rd_loop/conf.py`，采用 Pydantic Settings + 环境变量模式：

```python
class FactorBasePropSetting(BasePropSetting):
    # 各组件的类路径，可通过环境变量覆盖
    scen: str = "rdagent.scenarios.qlib.experiment.factor_experiment.QlibFactorScenario"
    hypothesis_gen: str = "rdagent.scenarios.qlib.proposal.factor_proposal.QlibFactorHypothesisGen"
    hypothesis2experiment: str = "...QlibFactorHypothesis2Experiment"
    coder: str = "...QlibFactorCoSTEER"
    runner: str = "...QlibFactorRunner"
    summarizer: str = "...QlibFactorExperiment2Feedback"
    
    # 回测时间范围
    train_start: str = "2008-01-01"
    train_end: str = "2014-12-31"
    valid_start: str = "2015-01-01"
    valid_end: str = "2016-12-31"
    test_start: str = "2017-01-01"
    test_end: str = "2020-08-01"
```

这意味着所有核心组件都可以通过环境变量替换为我们自定义的实现。

#### 2.4.2 因子假设生成

`QlibFactorHypothesisGen` 继承自 `FactorHypothesisGen`，核心方法：

- **`prepare_context()`**：构建 LLM 提示上下文，包括历史假设和反馈、RAG 知识、输出格式要求
- **`convert_response()`**：将 LLM 的 JSON 响应解析为 `Hypothesis` 对象

关键设计：当迭代轮数 < 15 时，引导 LLM 尝试简单因子；超过 15 轮后引导尝试机器学习类因子。

#### 2.4.3 因子实验执行

`QlibFactorRunner` 是因子回测的核心：

1. 处理 SOTA 因子与新因子的组合
2. 使用 IC（信息系数）去重，IC > 0.99 的因子被过滤
3. 因子数据保存为 parquet 格式
4. 通过 Docker 容器中的 Qlib 执行回测（`qrun` 命令）
5. 结果保存为 `qlib_res.csv` 和 `ret.pkl`

**Docker 环境配置**：
```python
# QlibFBWorkspace.execute() 
if MODEL_COSTEER_SETTINGS.env_type == "docker":
    qtde = QTDockerEnv()
elif MODEL_COSTEER_SETTINGS.env_type == "conda":
    qtde = QlibCondaEnv(conf=QlibCondaConf())
```

RD-Agent 同时支持 Docker 和 Conda 两种执行环境，这为我们提供了灵活的部署选择。

#### 2.4.4 Quant 联合优化

`fin_quant` 命令启动因子-模型联合优化（QuantBasePropSetting），使用多臂赌博机（bandit）策略在因子优化和模型优化之间自动选择：

```python
class QuantBasePropSetting(BasePropSetting):
    action_selection: str = "bandit"  # 'bandit' | 'llm' | 'random'
    # 同时配置了 factor_* 和 model_* 两套组件
```

### 2.5 LLM 配置系统

RD-Agent 使用 LiteLLM 作为默认后端，配置通过 `.env` 文件和环境变量完成：

```python
class LLMSettings(ExtendedBaseSettings):
    backend: str = "rdagent.oai.backend.LiteLLMAPIBackend"
    chat_model: str = "gpt-4-turbo"
    embedding_model: str = "text-embedding-3-small"
    reasoning_think_rm: bool = False  # 移除 <think> 标签
    chat_temperature: float = 0.5
    max_retry: int = 10
```

**DeepSeek 配置方案**（官方支持）：

```bash
# .env 文件
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=<your_key>

# Embedding 使用 SiliconFlow
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=<your_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
```

### 2.6 Web UI 与 Flask 后端

RD-Agent 提供两套 UI：

1. **Streamlit UI**（`rdagent ui`）：适合 data_science 场景，通过 `rdagent.log.ui.app` 启动
2. **Web UI**（`rdagent server_ui`）：Flask 后端 + Vue.js 前端，支持实时交互

**Flask 后端的关键 API**（`rdagent/log/server/app.py`）：

| 端点 | 方法 | 功能 |
|------|------|------|
| `/upload` | POST | 启动新的 RD-Agent 任务（指定场景、参数） |
| `/trace` | POST | 获取指定 trace 的消息流（增量或全量） |
| `/traces` | GET | 列出所有历史 trace |
| `/control` | POST | 控制进程（stop） |
| `/user_interaction/submit` | POST | 提交用户交互响应 |
| `/receive` | POST | 接收前端消息 |
| `/stdout` | GET | 下载进程 stdout 日志 |

**关键发现**：Flask 后端通过 `RDAgentTask` 类管理子进程，每个任务在独立的 `multiprocessing.Process` 中运行，通过 `Queue` 实现用户交互。这意味着 **RD-Agent 的 Flask 后端本身就是一个任务编排器**，可以被外部系统通过 HTTP API 调用。

### 2.7 CLI 接口

RD-Agent 的 CLI 基于 Typer 框架（`rdagent/app/cli.py`），主要命令：

```bash
# 量化场景
rdagent fin_factor              # 因子自动进化循环
rdagent fin_model               # 模型自动进化循环
rdagent fin_quant               # 因子+模型联合进化
rdagent fin_factor_report       # 从财报提取因子

# 其他场景
rdagent data_science            # 数据科学/Kaggle
rdagent general_model <URL>     # 论文模型复现
rdagent llm_finetune            # LLM 微调

# UI 和工具
rdagent ui                      # Streamlit UI
rdagent server_ui               # Flask Web UI
rdagent health_check            # 健康检查
```

所有场景命令支持 `--loop_n`、`--step_n`、`--all_duration` 参数控制运行规模，以及 `--checkout/--no-checkout` 控制断点续跑。

---

## 3. OpenClaw 编排能力概览

### 3.1 多 Agent 架构

OpenClaw 的核心价值在于其多 Agent 编排层：

- **Session 管理**：每个 Agent 运行在独立的 Session 中，支持 spawn（生成子 Agent）、history（历史查询）、message passing（消息传递）
- **ACP 协议**：标准化的 Agent 通信协议，支持跨平台 Agent 协作（Claude Code、Cursor、OpenCode 等）
- **Cron 调度**：精确定时任务，支持一次性/周期性任务，可指定不同模型和思考级别
- **任务中心 Dashboard**：可视化编排和监控，跟踪任务状态和 Agent 产出
- **Heartbeat 心跳**：周期性检查机制，支持邮件、日历、天气等主动检查

### 3.2 现有量化基础设施

基于对 OpenClaw 实际环境的扫描分析：

- **SSH/Zerotier 连接**：VPS 到群晖 NAS（`10.12.192.241`）和 HP 工作站的远程执行通道
- **quant-compute Agent**：已有量化计算 Agent（使用 deepseek-v4-flash 主力模型），可执行因子研究和回测
- **factor_db.sqlite**：当前 **尚未建立**，需要作为本方案的一部分创建
- **quant-evolve 项目**：当前 **尚未建立**，本方案将定义其初始结构
- **通信渠道**：已配置微信（openclaw-weixin）、QQ Bot 和 lightclawbot 三个通知渠道
- **任务中心**：独立 Node.js 服务（端口 8055），提供 REST API 进行任务 CRUD
- **ACP 协议**：默认 Agent 为 claude，支持 claude/codex/gemini/opencode
- **模型配置**：主力 glm-5.2（智谱），备选 deepseek-v4-flash/pro，ACP 模型通过火山方舟
- **子 Agent 编排**：最大 8 并发，4 层深度，2400 秒超时，支持 fork/isolated 两种上下文模式

### 3.3 编排优势

OpenClaw 相对 RD-Agent 内部循环的编排优势：

| 能力 | OpenClaw | RD-Agent 内部 |
|------|----------|---------------|
| 多角色协作 | ✅ 原生支持（6 个 Agent + ACP） | ❌ 单循环内的固定步骤 |
| 外部通知 | ✅ 微信/QQ/lightclawbot 三渠道 | ❌ 仅 UI 展示 |
| 定时调度 | ✅ Cron + Heartbeat（30min） | ❌ 仅 loop_n/duration |
| 任务监控 | ✅ 任务中心 API（端口 8055）+ Dashboard | ⚠️ 仅有日志/trace |
| 断点续跑 | ✅ Session 持久化 | ✅ Session pickle |
| 人工介入 | ✅ 自然语言交互 | ⚠️ 需要 UI 交互 |
| 多场景编排 | ✅ 跨场景任务流（190+ 研报） | ❌ 单场景循环 |
| 子 Agent 并发 | ✅ 最大 8 并发、4 层深度 | ⚠️ 仅 step_semaphore 并行 |
| ACP 协议 | ✅ claude/codex/gemini/opencode | ❌ 无 |

---

## 4. 三种结合方案设计

### 4.1 方案 A：OpenClaw 编排 + RD-Agent CLI 执行（推荐 MVP）

#### 架构概述

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw 编排层                        │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ main     │→ │ quant-       │→ │ Dashboard       │   │
│  │ (秘书)   │  │ compute      │  │ (监控+通知)      │   │
│  └──────────┘  └──────┬───────┘  └─────────────────┘   │
│                       │ SSH                              │
├───────────────────────┼─────────────────────────────────┤
│                       ▼                                  │
│              本地 HP 工作站                               │
│  ┌──────────────────────────────────┐                    │
│  │  RD-Agent CLI 执行               │                    │
│  │  $ rdagent fin_factor \          │                    │
│  │      --loop_n 10 \               │                    │
│  │      --checkout                  │                    │
│  │  (conda quant 环境)              │                    │
│  └──────────────┬───────────────────┘                    │
│                 ▼                                        │
│  ┌──────────────────────────────────┐                    │
│  │  Qlib Docker 容器                │                    │
│  │  (因子回测执行)                   │                    │
│  └──────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

#### 工作流程

1. **任务提交**：用户通过 OpenClaw main Agent 提交因子研究任务（自然语言或命令）
2. **任务分发**：main Agent 将任务路由到 quant-compute Agent
3. **SSH 执行**：quant-compute 通过 SSH 连接本地 HP，在 conda quant 环境中执行 `rdagent fin_factor` 命令
4. **参数传递**：通过命令行参数控制循环次数、时间范围等
5. **进度监控**：quant-compute 定期检查 RD-Agent 的日志输出，汇报给任务中心
6. **结果回传**：RD-Agent 完成后，因子代码和回测结果回传
7. **审核入库**：结果经 research-lead Agent 审核，优秀因子入库
8. **通知反馈**：微信通知用户任务完成

#### 关键实现

```bash
# quant-compute Agent 执行的 SSH 命令模板
ssh hp-workstation 'cd ~/quant && conda activate quant && \
  rdagent fin_factor \
    --loop_n 10 \
    --all_duration 8h \
    --checkout \
  2>&1 | tee logs/rdagent_$(date +%Y%m%d_%H%M%S).log'
```

#### 优缺点

**优点：**
- 实现最简单，RD-Agent 零修改
- 充分利用 OpenClaw 的 SSH 通道和任务中心
- 快速验证可行性，1-2 天可跑通 MVP
- RD-Agent 独立运行，互不干扰

**缺点：**
- 过程中缺乏细粒度交互（只能等 RD-Agent 跑完）
- RD-Agent 的 trace 信息无法实时展示在 Dashboard
- 因子去重和审核需要人工介入
- 无法利用 RD-Agent 的 Web UI 交互能力

**实现难度：** ⭐⭐（低）  
**维护成本：** ⭐⭐（低）  
**推荐度：** ⭐⭐⭐⭐⭐（MVP 首选）

---

### 4.2 方案 B：RD-Agent 作为独立服务 + OpenClaw API 触发

#### 架构概述

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw 编排层                         │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ main     │→ │ quant-       │→ │ Dashboard          │    │
│  │ (秘书)   │  │ compute      │  │ (嵌入RD-Agent UI)  │    │
│  └──────────┘  └──────┬───────┘  └────────────────────┘    │
│                       │ HTTP API                            │
├───────────────────────┼─────────────────────────────────────┤
│                       ▼                                      │
│              本地 HP 工作站                                   │
│  ┌────────────────────────────────────────────────┐         │
│  │  RD-Agent Flask Server (port 19899)            │         │
│  │  ┌──────────────────────────────────────────┐  │         │
│  │  │  POST /upload   → 启动进化循环            │  │         │
│  │  │  POST /trace    → 获取实时 trace          │  │         │
│  │  │  POST /control  → 停止任务               │  │         │
│  │  │  GET  /traces   → 列出历史               │  │         │
│  │  │  Vue.js 前端 (iframe 嵌入 Dashboard)     │  │         │
│  │  └──────────────────────────────────────────┘  │         │
│  │                                                │         │
│  │  ┌──────────────────────────────────────────┐  │         │
│  │  │  RD-Agent Worker Process                 │  │         │
│  │  │  (因子进化循环 in Docker)                 │  │         │
│  │  └──────────────────────────────────────────┘  │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

#### 工作流程

1. **服务常驻**：RD-Agent Flask Server 在本地 HP 上持续运行（systemd 或 tmux）
2. **API 触发**：OpenClaw quant-compute Agent 通过 HTTP POST 触发进化循环
3. **实时追踪**：quant-compute 定期调用 `/trace` API 获取进度，转发到 Dashboard
4. **UI 嵌入**：RD-Agent 的 Vue.js Web UI 通过 iframe 嵌入 OpenClaw Dashboard
5. **结果入库**：循环结束后，自动解析结果并写入 factor_db
6. **通知反馈**：OpenClaw 微信通知用户

#### 关键实现

```python
# quant-compute Agent 触发 RD-Agent 的伪代码
import requests

HP_RDAGENT_URL = "http://hp-workstation:19899"

def start_factor_evolution(
    loops: int = 10,
    duration_hours: int = 8,
    base_features: dict = None,
):
    """通过 API 启动因子进化循环"""
    files = {}
    if base_features:
        # 上传基础因子文件
        files = prepare_feature_files(base_features)
    
    response = requests.post(f"{HP_RDAGENT_URL}/upload", data={
        "scenario": "Finance Data Building",
        "loops": loops,
        "all_duration": duration_hours,
    }, files=files)
    
    trace_id = response.json()["id"]
    return trace_id

def poll_trace(trace_id: str) -> list:
    """获取增量 trace 消息"""
    response = requests.post(f"{HP_RDAGENT_URL}/trace", json={
        "id": trace_id,
        "all": False,
    })
    return response.json()

def stop_task(trace_id: str):
    """停止任务"""
    requests.post(f"{HP_RDAGENT_URL}/control", json={
        "id": trace_id,
        "action": "stop",
    })
```

#### Dashboard iframe 嵌入

```html
<!-- OpenClaw Dashboard 中的 RD-Agent 面板 -->
<iframe 
  src="http://hp-workstation:19899/"
  style="width:100%; height:800px; border:none;"
  title="RD-Agent Monitor"
></iframe>
```

#### 优缺点

**优点：**
- 利用 RD-Agent 原生 Flask API，开发量中等
- 实时获取 trace 信息（假设、代码、反馈）
- RD-Agent Web UI 可视化进化过程，体验好
- 支持用户通过 RD-Agent UI 交互（修改假设等）
- 一个 Flask Server 可管理多个并行 trace

**缺点：**
- 需要 HP 上长期运行 Flask Server（资源占用）
- 需要处理跨域、认证等 Web 安全问题
- iframe 嵌入可能有跨域限制
- trace 数据格式需要适配到 OpenClaw Dashboard
- HP 需要暴露端口或通过反向代理

**实现难度：** ⭐⭐⭐（中）  
**维护成本：** ⭐⭐⭐（中）  
**推荐度：** ⭐⭐⭐⭐（第二阶段首选）

---

### 4.3 方案 C：深度融合 — 模块映射架构

#### 架构概述

```
┌─────────────────────────────────────────────────────────────────┐
│                    OpenClaw 融合编排层                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │           Quant Research Team (多Agent协作)           │       │
│  │                                                       │       │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │       │
│  │  │ factor-     │→ │ factor-      │→ │ factor-     │ │       │
│  │  │ proposer    │  │ coder        │  │ evaluator   │ │       │
│  │  │ (假设生成)  │  │ (代码实现)   │  │ (回测评估)  │ │       │
│  │  └─────────────┘  └──────────────┘  └─────────────┘ │       │
│  │         ↑                                    ↓       │       │
│  │  ┌─────────────┐                   ┌─────────────┐  │       │
│  │  │ knowledge-  │←──────────────────│ factor-     │  │       │
│  │  │ manager     │   (反馈循环)       │ reviewer    │  │       │
│  │  │ (知识库)    │                   │ (审核入库)  │  │       │
│  │  └─────────────┘                   └─────────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                Orchestrator (编排器)                   │       │
│  │  - Session 管理（替代 LoopBase）                      │       │
│  │  - Cron 调度（替代 loop_n/duration）                  │       │
│  │  - Dashboard 监控（替代 Streamlit UI）                │       │
│  │  - 微信通知                                           │       │
│  └──────────────────────────────────────────────────────┘       │
├──────────────────────────────────────────────────────────────────┤
│                   本地 HP 计算节点                                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │  Qlib Docker (仅回测执行)                              │       │
│  └──────────────────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────────────────┘
```

#### 模块映射关系

将 RD-Agent 的核心模块拆解，映射为 OpenClaw 的独立 Agent：

| RD-Agent 模块 | OpenClaw Agent | 职责 | RD-Agent 源码参考 |
|---------------|----------------|------|-------------------|
| `QlibFactorHypothesisGen` | `factor-proposer` | 生成因子假设 | `scenarios/qlib/proposal/factor_proposal.py` |
| `FactorCoSTEER` | `factor-coder` | 实现因子代码 | `components/coder/factor_coder/` |
| `QlibFactorRunner` | `factor-evaluator` | 执行回测、收集结果 | `scenarios/qlib/developer/factor_runner.py` |
| `QlibFactorExperiment2Feedback` | `factor-reviewer` | 评估反馈、决策 | `scenarios/qlib/developer/feedback.py` |
| `EvolvingKnowledgeBase` | `knowledge-manager` | 知识库管理 | `core/knowledge_base.py` |
| `LoopBase` 编排 | OpenClaw Orchestrator | 调度、session、通知 | `utils/workflow/loop.py` |

#### 工作流程

1. **Orchestrator 启动**：OpenClaw 编排器根据 Cron 或手动触发，创建一轮进化任务
2. **假设生成**：`factor-proposer` Agent 接收历史 trace（从 knowledge-manager 获取），调用 LLM 生成新假设
3. **代码实现**：假设传递给 `factor-coder` Agent，生成因子代码（可使用 claude-code-local Agent）
4. **回测执行**：代码传递给 `factor-evaluator` Agent，通过 SSH 在 HP 的 Qlib Docker 中执行回测
5. **审核评估**：结果传递给 `factor-reviewer` Agent，生成评估反馈
6. **知识更新**：反馈回流到 `knowledge-manager`，更新知识库和 trace
7. **循环迭代**：Orchestrator 根据反馈决定继续/停止/调整方向
8. **结果入库**：优秀因子写入 factor_db，微信通知用户

#### 关键设计：Trace 在 Agent 间传递

```python
# Orchestrator 中的 trace 管理
class EvolutionTrace:
    """跨 Agent 共享的进化 trace"""
    loop_id: int
    hypothesis: dict        # factor-proposer 输出
    experiment: dict        # factor-coder 输出
    code_workspace: dict    # 代码文件
    backtest_result: dict   # factor-evaluator 输出
    feedback: dict          # factor-reviewer 输出
    
    def to_context(self) -> str:
        """转换为下一轮 LLM 的上下文"""
        ...
```

#### 优缺点

**优点：**
- 最大灵活性，每个环节可独立优化和替换
- 充分利用 OpenClaw 的多 Agent 协作能力
- 可以在不同环节使用不同的 LLM（如假设生成用 DeepSeek-R1，代码实现用 Claude）
- 天然支持人工介入（任何一步都可以暂停等人审核）
- 知识库可以跨场景复用
- 可扩展性强，容易添加新的 Agent 角色（如 model-optimizer）

**缺点：**
- 实现工作量最大（需要重写 RD-Agent 的循环逻辑）
- LLM 调用次数增加（Agent 间通信开销）
- 需要深入理解 RD-Agent 的 prompt 系统和知识库结构
- 调试复杂度高（多 Agent 链路追踪）
- 可能丢失 RD-Agent 内部的优化（如并行执行、session 持久化等）
- 维护成本最高

**实现难度：** ⭐⭐⭐⭐⭐（高）  
**维护成本：** ⭐⭐⭐⭐（高）  
**推荐度：** ⭐⭐⭐（长期目标，不适合 MVP）

---

### 4.4 三种方案对比总览

| 维度 | 方案 A (CLI 执行) | 方案 B (API 服务) | 方案 C (深度融合) |
|------|:-:|:-:|:-:|
| **实现周期** | 1-2 天 | 1-2 周 | 4-8 周 |
| **开发量** | 低 | 中 | 高 |
| **RD-Agent 修改** | 无 | 几乎无 | 大量重构 |
| **实时监控** | 仅日志 | trace + UI | 完全自定义 |
| **用户交互** | 任务级 | 步骤级（通过 UI） | 完全自定义 |
| **并行能力** | 单任务 | 多 trace | 多 Agent 并行 |
| **LLM 灵活性** | 固定 | 固定 | 每步可定制 |
| **维护难度** | 低 | 中 | 高 |
| **推荐阶段** | Phase 1 (MVP) | Phase 2 (增强) | Phase 3 (长期) |

**综合推荐结论：方案 A 作为 MVP 立即启动，方案 B 作为 2-4 周内的增强目标，方案 C 作为长期探索方向。**

---

## 5. 数据流设计

### 5.1 RD-Agent 数据需求分析

RD-Agent 的 Qlib 场景使用标准 Qlib 数据格式。从源码分析（`QlibFactorRunner.develop()` 和 `QlibFactorScenario`）：

**输入数据：**
- Qlib 格式的股票数据（通过 Qlib 的 `D.features()` API 获取）
- 因子表达式（Qlib Alpha 算子格式，如 `Resi($close, 5)/$close`）
- 因子代码文件（Python 文件，实现 `factor__name__()` 函数）
- 配置 YAML（回测参数：时间范围、模型类型、超参数）

**输出数据：**

| 输出 | 格式 | 位置 | 用途 |
|------|------|------|------|
| 回测指标 | CSV (`qlib_res.csv`) | workspace 目录 | IC、年化收益、夏普比率等 |
| 收益曲线 | pickle (`ret.pkl`) | workspace 目录 | 净值曲线数据 |
| 因子数据 | parquet (`combined_factors_df.parquet`) | workspace 目录 | 因子值面板 |
| 执行日志 | 文本 (stdout) | trace 目录 | 训练过程日志 |
| Trace 消息 | pickle (`.pkl`) | `__session__/` | 假设、代码、反馈的完整记录 |

### 5.2 与现有数据格式兼容性

**现有 parquet 数据 → RD-Agent：**

现有的 quant 项目 parquet 文件（如有 A 股量价数据）可以通过 Qlib 的数据转换工具适配。RD-Agent 的 `QlibFBWorkspace` 通过 Qlib API 获取数据，因此关键是在 HP 上正确配置 Qlib 数据目录。

**关键适配点：**

```
现有 parquet 数据
    ↓ (Qlib dump 工具转换)
Qlib 数据格式 (~/.qlib/qlib_data/cn_data/)
    ↓ (RD-Agent 自动获取)
因子回测执行
    ↓ 
回测结果 (CSV + pickle)
    ↓ (OpenClaw 结果采集器)
Dashboard 展示 + factor_db 入库
```

### 5.3 因子库同步设计

RD-Agent 生成的因子需要同步到现有的 factor_db.sqlite。设计一个因子同步适配层：

```python
# 因子同步适配器（伪代码）
class FactorSyncAdapter:
    """将 RD-Agent 输出的因子同步到 factor_db.sqlite"""
    
    def __init__(self, factor_db_path: str, rdagent_trace_dir: str):
        self.factor_db = sqlite3.connect(factor_db_path)
        self.trace_dir = rdagent_trace_dir
    
    def extract_factors_from_trace(self, trace_id: str) -> list[dict]:
        """从 RD-Agent trace 中提取因子信息"""
        # 加载 trace pickle 文件
        # 解析每个 loop 的 workspace.file_dict
        # 提取因子代码和回测指标
        ...
    
    def sync_to_factor_db(self, factors: list[dict]):
        """将因子写入 factor_db"""
        for factor in factors:
            self.factor_db.execute(
                "INSERT OR REPLACE INTO factors "
                "(name, code, description, ic, sharpe, arr, source, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 'rdagent', ?)",
                (factor['name'], factor['code'], factor['description'],
                 factor['ic'], factor['sharpe'], factor['arr'],
                 datetime.now().isoformat())
            )
    
    def deduplicate(self, threshold: float = 0.99):
        """基于 IC 去重"""
        # RD-Agent 内部已有 IC > 0.99 去重
        # 这里做二次检查
        ...
```

### 5.4 完整数据流图

```
┌────────────────────────────────────────────────────────────────────┐
│                        数据流全景                                   │
│                                                                     │
│  ┌──────────┐     SSH/API      ┌──────────────┐                    │
│  │ OpenClaw │ ───────────────→ │  RD-Agent    │                    │
│  │ 任务参数  │                  │  (HP 上运行)  │                    │
│  └──────────┘                  └──────┬───────┘                    │
│                                       │                            │
│              ┌────────────────────────┼────────────────┐           │
│              ▼                        ▼                ▼           │
│     ┌──────────────┐     ┌──────────────┐   ┌──────────────┐      │
│     │ Qlib 数据    │     │ 因子代码     │   │ 回测结果     │      │
│     │ (~/.qlib/)   │     │ (*.py)       │   │ (CSV+pkl)    │      │
│     └──────────────┘     └──────────────┘   └──────┬───────┘      │
│                                                   │               │
│                                                   ▼               │
│     ┌──────────────┐                     ┌──────────────┐         │
│     │ factor_db    │ ←──── 同步 ──────── │ 结果解析器   │         │
│     │ .sqlite      │                     │ (OpenClaw)   │         │
│     └──────┬───────┘                     └──────────────┘         │
│            │                                                       │
│            ▼                                                       │
│     ┌──────────────┐     ┌──────────────┐   ┌──────────────┐      │
│     │ Dashboard    │────→│ 微信通知     │   │ 邮件报告     │      │
│     │ (可视化)     │     │ (即时提醒)   │   │ (详细摘要)   │      │
│     └──────────────┘     └──────────────┘   └──────────────┘      │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 6. 部署架构方案

### 6.1 部署位置决策：本地 HP vs VPS

**结论：RD-Agent 必须部署在本地 HP 工作站上。**

理由分析：

| 因素 | 本地 HP | VPS |
|------|---------|-----|
| Docker 支持 | ✅ 完全控制 | ⚠️ 可能受限 |
| CPU/内存 | ✅ 通常较强 | ⚠️ 受限于套餐 |
| Qlib 数据 | ✅ 已有本地数据 | ❌ 需要迁移 |
| 网络稳定性 | ✅ 本地执行不受影响 | ⚠️ API 调用需稳定网络 |
| 成本 | ✅ 无额外成本 | ❌ 高配 VPS 费用 |
| 可维护性 | ✅ 直接访问 | ⚠️ 需要远程管理 |
| LLM API 延迟 | ⚠️ 国内访问 DeepSeek 快 | ✅ 海外 API 快 |

### 6.2 Python 环境管理

RD-Agent 需要 Python 3.10 或 3.11（CI 测试版本），建议创建独立 conda 环境：

```bash
# 在 HP 上创建 RD-Agent 专用环境
conda create -n rdagent python=3.10
conda activate rdagent

# 安装 RD-Agent
pip install rdagent

# 或从源码安装（开发者模式）
git clone https://github.com/microsoft/RD-Agent
cd RD-Agent
make dev

# 与现有 quant 环境共存
# quant 环境 → 现有量化研究和数据维护
# rdagent 环境 → RD-Agent 自动进化循环
```

**环境隔离原则：**
- `quant` 环境：保留现有用途，手动因子研究、数据更新、Qlib 配置
- `rdagent` 环境：RD-Agent 专用，避免依赖冲突
- Docker 容器：Qlib 回测在 Docker 内执行，与 Host 环境隔离

### 6.3 资源消耗估算

基于 RD-Agent 的架构分析：

| 资源 | 最低要求 | 推荐配置 | 说明 |
|------|----------|----------|------|
| CPU | 4 核 | 8+ 核 | Docker 内模型训练（LightGBM/LSTM） |
| 内存 | 8 GB | 16+ GB | Qlib 数据加载 + Docker + Python 进程 |
| 磁盘 | 20 GB | 50+ GB | Qlib 数据 + Docker 镜像 + workspace + trace |
| GPU | 无需 | 可选 | 深度学习模型训练加速 |
| 网络 | 稳定 | 低延迟 | LLM API 调用（DeepSeek） |

**主要资源消耗项：**

1. **Qlib Docker 镜像**：约 5-8 GB 磁盘空间
2. **Qlib 数据**：A股全市场数据约 2-3 GB
3. **Workspace**：每轮循环生成临时文件，约 100-500 MB/轮
4. **Trace 日志**：pickle 文件，约 10-50 MB/轮
5. **LLM API 调用**：DeepSeek 成本约 $0.5-2/轮（含假设生成+代码实现+评估）

### 6.4 项目目录规划

由于 `factor_db.sqlite` 和 `quant-evolve` 项目当前均不存在，本方案将定义其初始结构：

```
~/quant/                          # 量化项目根目录（新建）
├── factor_db.sqlite              # 因子数据库（新建）
├── data/                         # 数据目录
│   ├── raw/                      # 原始数据（parquet）
│   └── qlib_format/              # Qlib 格式数据
├── rdagent/                      # RD-Agent 项目目录（新增）
│   ├── .env                      # RD-Agent 配置
│   ├── log/                      # 运行日志
│   ├── git_ignore_folder/        # 工作区+trace
│   │   ├── RD-Agent_workspace/   # 因子工作区
│   │   ├── traces/               # 进化 trace
│   │   └── static/               # Web UI 静态文件
│   ├── pickle_cache/             # 缓存
│   └── start_server.sh           # Flask Server 启动脚本
└── .qlib/                        # Qlib 数据（共享）
    └── qlib_data/
        └── cn_data/              # A股数据
```

**Docker 环境配置选择：**

RD-Agent 支持两种执行环境（`MODEL_COSTEER_SETTINGS.env_type`）：

```bash
# 方式 1：Docker（推荐，完全隔离）
# .env 文件
MODEL_CODER_ENV_TYPE=docker

# 方式 2：Conda（轻量，复用本地 Qlib）
# .env 文件
MODEL_CODER_ENV_TYPE=conda
```

推荐使用 Conda 模式（复用本地 Qlib 数据，避免 Docker 数据迁移），如果遇到依赖冲突再切换到 Docker 模式。

### 6.5 网络架构

```
┌──────────────────────────────────────────────────────┐
│                   网络拓扑                            │
│                                                       │
│  ┌──────────┐         ┌──────────────────────────┐   │
│  │ OpenClaw │  SSH /  │    本地 HP 工作站         │   │
│  │   VPS    │  Zerotier │  (192.168.x.x)         │   │
│  │ (云端)   │────────→│                          │   │
│  └──────────┘         │  ┌────────────────────┐  │   │
│       │               │  │ RD-Agent Flask     │  │   │
│       │               │  │ Server :19899      │  │   │
│       │    HTTP       │  └────────────────────┘  │   │
│       └──────────────→│  ┌────────────────────┐  │   │
│           (API 调用)   │  │ Qlib Docker/Conda  │  │   │
│                       │  │ (回测执行)         │  │   │
│                       │  └────────────────────┘  │   │
│                       │                           │   │
│                       │  ┌────────────────────┐  │   │
│                       │  │ DeepSeek API 调用  │ ←──── 外网
│                       │  └────────────────────┘  │   │
│                       └──────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**端口规划：**
- `19899`：RD-Agent Flask Server（Web UI + API）
- `19900`：RD-Agent Data Science 交互 UI（可选）
- Zerotier 虚拟网络：VPS ↔ HP 通信通道

---

## 7. 实施路径与里程碑

### 7.1 Phase 1：MVP 验证（1-2 周）

**目标：** 跑通 RD-Agent 基础循环，验证技术可行性

**采用方案：** 方案 A（CLI 执行）

**任务清单：**

| 序号 | 任务 | 工作量 | 产出 |
|------|------|--------|------|
| 1.1 | HP 上安装 RD-Agent | 0.5 天 | conda 环境 + pip install |
| 1.2 | 配置 DeepSeek API | 0.5 天 | .env 文件 + health_check 通过 |
| 1.3 | 配置 Qlib 数据 | 1 天 | A股数据就绪，qrun 可执行 |
| 1.4 | 手动跑通 fin_factor | 0.5 天 | 1-3 轮进化循环成功 |
| 1.5 | OpenClaw SSH 触发 | 0.5 天 | quant-compute Agent 执行 rdagent 命令 |
| 1.6 | 结果回传和通知 | 0.5 天 | 因子代码+回测指标回传 OpenClaw |
| 1.7 | Dashboard 展示 | 0.5 天 | 基础结果显示 |

**验收标准：**
- OpenClaw 通过 quant-compute Agent 触发 RD-Agent 因子进化
- RD-Agent 在 HP 上成功完成至少 3 轮进化
- 因子代码和回测指标能回传到 OpenClaw
- 微信通知用户任务完成

### 7.2 Phase 2：服务化集成（2-4 周）

**目标：** 实现实时监控和交互能力

**采用方案：** 方案 B（API 服务）

**任务清单：**

| 序号 | 任务 | 工作量 | 产出 |
|------|------|--------|------|
| 2.1 | Flask Server 部署 | 1 天 | systemd 服务 + 自启动 |
| 2.2 | API 对接 | 2 天 | quant-compute 调用 /upload + /trace |
| 2.3 | Trace 解析器 | 2 天 | 解析假设/代码/反馈消息 |
| 2.4 | Dashboard 面板 | 2 天 | iframe 嵌入 + 自定义面板 |
| 2.5 | 因子同步适配器 | 1 天 | factor_db.sqlite 自动入库 |
| 2.6 | 安全加固 | 1 天 | 认证 token + 跨域配置 |
| 2.7 | 并行 trace 管理 | 2 天 | 多任务同时运行 |
| 2.8 | fin_quant 联合优化 | 1 天 | 因子+模型联合进化 |

**验收标准：**
- RD-Agent Flask Server 作为常驻服务运行
- OpenClaw Dashboard 实时展示进化进度
- 因子自动入库 factor_db.sqlite
- 支持因子+模型联合优化

### 7.3 Phase 3：深度融合（6-12 周，可选）

**目标：** 构建完整的量化研发 Agent 团队

**采用方案：** 方案 C（模块映射）

**任务清单：**

| 序号 | 任务 | 工作量 | 产出 |
|------|------|--------|------|
| 3.1 | Agent 角色定义 | 1 周 | factor-proposer/coder/evaluator/reviewer |
| 3.2 | Prompt 系统迁移 | 1 周 | RD-Agent 的 prompts.yaml 迁移到 OpenClaw |
| 3.3 | 知识库适配 | 1 周 | trace 持久化 + 知识库管理 |
| 3.4 | 多 LLM 策略 | 0.5 周 | 不同环节使用不同 LLM |
| 3.5 | 人工介入机制 | 0.5 周 | 暂停/审核/修改流程 |
| 3.6 | 模型优化 Agent | 1 周 | 添加 model-optimizer 角色 |
| 3.7 | 跨场景知识复用 | 1 周 | 研究知识库共享 |
| 3.8 | 完整文档和测试 | 1 周 | 运维文档 + 集成测试 |

**验收标准：**
- 每个环节由独立 Agent 执行
- 可在不同环节使用不同 LLM
- 支持人工介入和审核
- 知识库跨场景复用

### 7.4 渐进式演进路线图

```
Phase 1 (MVP)                Phase 2 (服务化)              Phase 3 (融合)
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Week 1-2        │    │ Week 3-6        │    │ Week 7-18       │
│                 │    │                 │    │                 │
│ • CLI 执行      │───→│ • Flask API     │───→│ • 多Agent协作   │
│ • 基础回测      │    │ • 实时监控      │    │ • 多LLM策略     │
│ • 结果通知      │    │ • 因子入库      │    │ • 人工介入      │
│                 │    │ • UI 嵌入       │    │ • 跨场景复用    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
      ⭐⭐⭐⭐⭐              ⭐⭐⭐⭐              ⭐⭐⭐
      立即启动               Phase 1 验收后            Phase 2 稳定后
```

---

## 8. 风险评估与应对

### 8.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| DeepSeek API 限流 | 高 | 中 | 配置 max_retry=10 + retry_wait；备用 API 切换 |
| Docker 环境冲突 | 中 | 高 | 使用 Conda 模式作为后备 |
| Qlib 数据格式不兼容 | 中 | 高 | 使用 Qlib 官方 dump 工具转换 |
| LLM 生成的因子代码报错 | 高 | 低 | RD-Agent 已有 skip_loop_error 机制 |
| HP 资源不足 | 中 | 中 | 监控 CPU/内存，限制并行度 |
| 网络不稳定导致 API 失败 | 中 | 中 | LiteLLM 后端自带重试机制 |

### 8.2 架构风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| RD-Agent 大版本升级破坏兼容 | 低 | 高 | 锁定版本 + fork 维护 |
| OpenClaw Agent 通信延迟 | 低 | 低 | 异步消息 + 超时机制 |
| 方案 C 重构工作量超预期 | 高 | 高 | 渐进式实施，先 A 后 B 再 C |
| 安全风险（Flask API 暴露） | 中 | 高 | token 认证 + 内网访问限制 |

### 8.3 运营风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| LLM API 成本失控 | 中 | 中 | 设置 loop_n/duration 上限 |
| 生成因子过拟合 | 高 | 高 | RD-Agent 内置 IC 去重 + 样本外验证 |
| 因子库膨胀 | 中 | 低 | 定期清理低效因子 |
| 无人值守时任务异常 | 中 | 中 | 微信告警 + 自动停止机制 |

---

## 9. 总结与建议

### 9.1 核心结论

1. **RD-Agent 是当前最成熟的自动研发框架**，其在 MLE-bench 排名第一和 NeurIPS 2025 发表证明了技术实力。Qlib 量化场景直接可用，不需要从零构建。

2. **OpenClaw 与 RD-Agent 的互补性极强**。OpenClaw 擅长多 Agent 编排、任务调度、外部通知和人工交互；RD-Agent 擅长自动化的假设-编码-验证-反馈循环。两者结合可以构建比任何单一系统都强大的量化研发体系。

3. **RD-Agent 的 Flask 后端是一个意外的惊喜**。它已经提供了完整的 HTTP API（`/upload`、`/trace`、`/control`），并且支持多任务并行管理。这使得方案 B（API 服务）的实现成本远低于预期。

4. **RD-Agent 的配置系统非常灵活**。所有核心组件（场景、假设生成器、编码器、运行器、评估器）都通过环境变量可配置替换，这为方案 C（深度融合）提供了技术可行性。

### 9.2 推荐实施路径

**立即行动（本周）：**
- 在 HP 上安装 RD-Agent，配置 DeepSeek API
- 手动跑通 `rdagent fin_factor --loop_n 3`，验证基础功能
- 通过 OpenClaw SSH 通道触发执行，验证方案 A 可行性

**短期（2-4 周）：**
- 实现 Phase 1 MVP，quant-compute Agent 集成 RD-Agent CLI
- 同时启动 Flask Server，验证 API 调用链路
- 建立因子从 RD-Agent 到 factor_db 的同步管道

**中期（4-8 周）：**
- 完成 Phase 2 服务化集成
- Dashboard 嵌入 RD-Agent UI
- 启动因子+模型联合优化（`fin_quant`）

**长期（8+ 周，视需求）：**
- 评估是否需要 Phase 3 深度融合
- 根据实际使用体验决定是否拆分 Agent 角色
- 探索跨场景知识复用（量化 → 研报 → 模型优化）

### 9.3 关键配置参考

**RD-Agent .env 文件模板（DeepSeek + SiliconFlow Embedding）：**

```bash
# LLM 配置
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=<your_deepseek_api_key>

# Embedding 配置
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=<your_siliconflow_api_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1

# 移除 reasoning think 标签（如使用 R1 模型）
REASONING_THINK_RM=True

# 执行环境（Conda 模式，复用本地 Qlib）
MODEL_CODER_ENV_TYPE=conda

# 并行度
STEP_SEMAPHORE=1

# 工作区路径
WORKSPACE_PATH=git_ignore_folder/RD-Agent_workspace
```

### 9.4 最终推荐

**推荐方案 A 作为 MVP**（1-2 天可跑通），**方案 B 作为中期目标**（2-4 周完成），方案 C 作为长期探索方向。

核心原则：**不要重新发明轮子**。RD-Agent 已经解决了自动研发循环的核心问题，OpenClaw 的价值在于编排和增强，而非替代。先用最简单的方式验证价值，再逐步深化集成。

---

## 附录 A：RD-Agent 核心组件类图

```
LoopBase (utils/workflow/loop.py)
  └── RDLoop (components/workflow/rd_loop.py)
        ├── hypothesis_gen: HypothesisGen
        │     └── QlibFactorHypothesisGen
        ├── hypothesis2experiment: Hypothesis2Experiment
        │     └── QlibFactorHypothesis2Experiment
        ├── coder: Developer (CoSTEER)
        │     └── FactorCoSTEER → QlibFactorCoSTEER
        ├── runner: Developer (Runner)
        │     └── CachedRunner → QlibFactorRunner
        ├── summarizer: Experiment2Feedback
        │     └── QlibFactorExperiment2Feedback
        └── trace: Trace
              └── (experiment, feedback)[]

Experiment (core/experiment.py)
  ├── sub_tasks: Task[]
  ├── sub_workspace_list: Workspace[]
  ├── experiment_workspace: FBWorkspace
  │     └── QlibFBWorkspace
  ├── based_experiments: Experiment[]
  └── hypothesis: Hypothesis

FBWorkspace (core/experiment.py)
  ├── file_dict: dict[str, str]
  ├── workspace_path: Path
  ├── execute(env, entry) → stdout
  └── inject_files(**files)
```

## 附录 B：Flask API 消息格式参考

**假设消息 (research.hypothesis)：**
```json
{
    "tag": "research.hypothesis",
    "timestamp": "2026-08-10T02:00:00Z",
    "loop_id": "1",
    "content": {
        "hypothesis": "基于成交量异常放大的因子可能捕捉到主力资金流入信号",
        "reason": "...",
        "concise_reason": "volume spike → smart money signal",
        "concise_observation": "...",
        "concise_knowledge": "..."
    }
}
```

**代码消息 (evolving.codes)：**
```json
{
    "tag": "evolving.codes",
    "loop_id": "1",
    "evo_id": "0",
    "content": [{
        "target_task_name": "volume_spike_factor",
        "workspace": {
            "factor.py": "def factor__volume_spike(df): ..."
        }
    }]
}
```

**反馈消息 (feedback.metric)：**
```json
{
    "tag": "feedback.metric",
    "loop_id": "1",
    "content": {
        "result": "{ \"IC\": 0.045, \"IR\": 0.32, \"Sharpe\": 1.8 }"
    }
}
```

## 附录 C：参考文献

- RD-Agent 技术报告：[R&D-Agent: An LLM-Agent Framework Towards Autonomous Data Science](https://arxiv.org/abs/2505.14738)
- RD-Agent(Q) 量化论文（NeurIPS 2025）：[R&D-Agent-Quant](https://arxiv.org/abs/2505.15155)
- 数据中心 R&D 基准：[Towards Data-Centric Automatic R&D](https://arxiv.org/abs/2404.11276)
- 协作进化策略：[Collaborative Evolving Strategy](https://arxiv.org/abs/2407.18690)
- RD-Agent 官方文档：https://rdagent.readthedocs.io/
- RD-Agent GitHub：https://github.com/microsoft/RD-Agent
- Qlib GitHub：https://github.com/microsoft/qlib

---

> **报告作者：** research-lead Agent  
> **审核状态：** 待审核  
> **最后更新：** 2026-08-10