# Microsoft RD-Agent 集成编排分析报告

> 研究时间：2026-08-10  
> 版本基准：RD-Agent v0.8.0 (PyPI 最新)  
> 仓库：https://github.com/microsoft/RD-Agent  
> 文档：https://rdagent.readthedocs.io/en/latest/

---

## 目录

1. [RD-Agent API/CLI 接口面](#1-rd-agentapicli-接口面)
2. [RD-Agent 输出格式](#2-rd-agent-输出格式)
3. [RD-Agent 部署要求](#3-rd-agent-部署要求)
4. [RD-Agent + 自定义 LLM 端点](#4-rd-agent--自定义-llm-端点)
5. [RD-Agent 可扩展性](#5-rd-agent-可扩展性)
6. [编排集成建议](#6-编排集成建议)

---

## 1. RD-Agent API/CLI 接口面

### 1.1 CLI 命令（主要交互方式）

RD-Agent 目前是一个 **纯 CLI 工具**，没有暴露 REST API 或 Webhook。所有场景通过 `rdagent` 命令行入口触发：

| 命令 | 用途 | 示例 |
|------|------|------|
| `rdagent fin_quant` | 启动量化因子/模型联合 R&D 循环 | 最核心的量化场景 |
| `rdagent fin_factor` | 仅运行因子挖掘循环 | 因子实验 |
| `rdagent fin_model` | 仅运行模型优化循环 | 模型实验 |
| `rdagent fin_factor_from_report` | 从研报提取因子 | 研报驱动的因子生成 |
| `rdagent data_science` | 通用数据科学 Agent | Kaggle/ML 任务 |
| `rdagent kaggle` | Kaggle 竞赛 Agent | 自动建模 |
| `rdagent finetune_llm` | LLM 微调 Agent | FT-Agent |
| `rdagent ui` | 启动 Web UI 可视化服务 | `rdagent ui --port 8080 --log-dir log/` |
| `rdagent health_check` | 环境健康检查 | 验证 Docker + 端口 |

**关键发现**：
- **没有内置 REST API / HTTP 服务端**用于程序化触发运行
- Web UI (`rdagent ui`) 仅用于**可视化日志**，不提供交互式控制 API
- 外部系统只能通过 **Shell 调用 CLI** 或 **Python import** 来触发

### 1.2 Python API（编程接口）

RD-Agent 的核心架构暴露了以下可编程的抽象类（`rdagent.core` 模块）：

```
rdagent.core.proposal
├── HypothesisGen(scen)        # 假设生成（R 角色）
│   └── gen(trace) → Hypothesis
├── Hypothesis2Experiment      # 假设转实验
│   └── convert(hypothesis, trace) → Experiment
├── ExpGen(scen)               # 实验生成器
│   ├── gen(trace) → Experiment
│   └── async_gen(trace, loop) → Experiment
├── ExpPlanner(scen)           # 实验规划器
│   └── plan(trace) → Plan
├── Experiment2Feedback(scen)  # 反馈生成
│   └── generate_feedback(exp, trace) → ExperimentFeedback
├── Trace(scen, knowledge_base) # R&D 轨迹管理
│   ├── get_sota_hypothesis_and_experiment()
│   ├── get_children(parent_idx)
│   └── sync_dag_parent_and_hist()
└── CheckpointSelector         # 检查点选择
```

**程序化触发方式**：
```python
# 可以直接 import 并组装组件
from rdagent.scenarios.qlib.proposal.quant_proposal import QlibQuantHypothesisGen
from rdagent.scenarios.qlib.developer.factor_coder import QlibFactorCoSTEER
from rdagent.scenarios.qlib.developer.factor_runner import QlibFactorRunner

# 在自己的编排脚本中组装 R&D 循环
```

### 1.3 编排集成可行性

| 集成方式 | 可行性 | 说明 |
|----------|--------|------|
| CLI Shell 调用 | ✅ 推荐 | 最简单，`subprocess` 即可 |
| Python import | ✅ 可行 | 深度集成，但需要理解内部 API |
| REST API | ❌ 不存在 | 需要自行封装 |
| Webhook | ❌ 不存在 | 需要自行封装 |
| 消息队列 | ❌ 不存在 | 需要自行封装 |

**建议**：对于编排平台，最佳路径是 **封装 CLI 为子进程** + **监控日志目录** 输出。

---

## 2. RD-Agent 输出格式

### 2.1 日志输出（主要产物）

RD-Agent 运行过程中的所有产物以**文件日志**形式存储，默认在 `log/` 目录下：

```
log/
├── <scenario>/
│   ├── session_<id>/
│   │   ├── loop_<n>/
│   │   │   ├── hypothesis.json      # 假设描述
│   │   │   ├── experiment.json      # 实验配置
│   │   │   ├── code/                # 生成的代码文件
│   │   │   │   ├── factor_v1.py     # 因子实现代码
│   │   │   │   └── model_v1.py      # 模型实现代码
│   │   │   ├── feedback.json        # 反馈结果
│   │   │   ├── trace.pkl            # Trace 对象（pickle 序列化）
│   │   │   └── output.log           # 运行日志
│   │   └── ...
│   └── ...
```

### 2.2 因子挖掘循环的输出

一个完整的因子挖掘循环（Fin-Factor 场景）产出包括：

| 产物类型 | 格式 | 内容 |
|----------|------|------|
| **因子代码** | `.py` 文件 | 可执行的 Qlib 因子实现，含 `Factor` 类 |
| **假设记录** | JSON/Pickle | 因子假设、推理过程、知识摘要 |
| **回测结果** | Qlib mlflow 格式 | IC、ICIR、ARR、Sharpe 等指标 |
| **实验反馈** | JSON | 决策（通过/拒绝）、代码变更摘要、EDA 改进建议 |
| **Trace 对象** | Pickle | 完整 R&D 轨迹（DAG 结构），可反序列化分析 |

### 2.3 模型优化循环的输出

- **模型代码**：Qlib 模型配置 + 训练脚本（`.py` / `.yaml`）
- **训练日志**：loss curve、metric 曲线（通过 Docker/Conda 执行）
- **性能指标**：与基线模型的对比结果

### 2.4 输出目录的自定义

通过环境变量 `LOG_FILE_PATH` 或 CLI 参数 `--log-dir` 指定输出路径，便于编排系统监控。

### 2.5 与外部系统对接的注意事项

- **没有结构化 JSON API** 输出最终结果
- 需要解析日志文件或反序列化 pickle 获取结构化数据
- Trace 对象使用 pickle 序列化，**跨语言读取困难**
- 因子代码是纯 Python 文件，可以直接被 Qlib 加载使用

---

## 3. RD-Agent 部署要求

### 3.1 系统要求

| 项目 | 要求 |
|------|------|
| **操作系统** | **仅支持 Linux**（官方明确声明） |
| **Python** | 3.10 或 3.11（CI 充分测试） |
| **Docker** | **必需**，当前用户必须能免 `sudo` 运行 |
| **内存** | 建议 16GB+（LLM 调用 + Docker 容器 + Qlib 数据） |
| **磁盘** | 建议 50GB+（Docker 镜像 + Qlib 数据 + 日志） |
| **GPU** | 非必需（RD-Agent 调用外部 LLM API） |

### 3.2 安装方式

```bash
# 方式一：PyPI 安装（推荐）
conda create -n rdagent python=3.10
conda activate rdagent
pip install rdagent

# 方式二：源码安装（开发模式）
git clone https://github.com/microsoft/RD-Agent
cd RD-Agent
make dev   # 安装依赖 + pre-commit hooks
```

### 3.3 依赖体系

核心依赖链：
```
rdagent
├── litellm              # LLM 后端统一接口（默认）
├── docker (SDK)         # 代码执行环境
├── pydantic             # 配置管理
├── pyqlib               # 量化回测引擎
├── numpy / pandas       # 数据处理
├── streamlit            # Web UI
├── rich                 # 终端日志美化
└── ...
```

### 3.4 能否与其他量化项目共存？

**可以**，但需注意：

1. **Conda 环境隔离**：建议独立 conda 环境，避免 `pyqlib` 版本冲突
2. **Docker 端口冲突**：RD-Agent 的 Web UI 默认端口需检查（`rdagent health_check` 会检测）
3. **Docker 资源**：RD-Agent 会动态创建/销毁 Docker 容器，确保 Docker daemon 有足够资源
4. **LLM API 配额**：多项目同时调用同一 LLM API 时需注意 rate limit
5. **文件系统**：日志目录、Qlib 数据目录建议明确区分

### 3.5 执行环境配置

RD-Agent 的代码执行支持两种模式（通过 `.env` 配置）：

```bash
# Docker 模式（推荐，隔离执行）
MODEL_COSTEER_ENV_TYPE=docker     # 模型场景
DS_CODER_COSTEER_ENV_TYPE=docker  # 数据科学场景

# Conda 模式（本地执行，适合调试）
MODEL_COSTEER_ENV_TYPE=conda
DS_CODER_COSTEER_ENV_TYPE=conda
```

---

## 4. RD-Agent + 自定义 LLM 端点

### 4.1 LLM 后端架构

RD-Agent **默认使用 LiteLLM** 作为 LLM 后端，这意味着它支持所有 LiteLLM 兼容的提供商（100+ providers）。配置通过 `.env` 文件完成。

### 4.2 DeepSeek 配置（官方完整示例）

```bash
# .env 文件
# CHAT MODEL: 使用 DeepSeek 官方 API
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=<your_deepseek_api_key>

# EMBEDDING MODEL: DeepSeek 无 embedding 模型，使用 SiliconFlow
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=<your_siliconflow_api_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
```

### 4.3 任意 OpenAI 兼容 API 配置

```bash
# .env 文件 - 通用 OpenAI 兼容端点
CHAT_MODEL=gpt-4o                    # 或任何模型名
OPENAI_API_BASE=<your_api_base>       # 如 http://localhost:8000/v1
OPENAI_API_KEY=<your_api_key>
```

### 4.4 分离 Chat / Embedding 端点

当 Chat 模型和 Embedding 模型来自不同提供商时：

```bash
# Chat Model
CHAT_MODEL=gpt-4o
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=<key>

# Embedding Model (不同提供商)
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-large-en-v1.5
LITELLM_PROXY_API_KEY=<other_key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
```

### 4.5 推理模型特殊配置

当使用包含思维链的推理模型（如 DeepSeek-R1）时：

```bash
REASONING_THINK_RM=True   # 去除 <think> 标签
```

### 4.6 Azure OpenAI 配置

```bash
CHAT_MODEL=azure/<deployment_name>
AZURE_API_BASE=https://<name>.openai.azure.com/
AZURE_API_KEY=<key>
AZURE_API_VERSION=2024-06-01
```

### 4.7 模型能力要求

RD-Agent 需要以下 LLM 能力：
1. **ChatCompletion**（对话补全）
2. **JSON Mode**（结构化输出）
3. **Embedding Query**（向量嵌入）

> ⚠️ 选择自定义 LLM 端点时，必须确认上述三项能力均可用。

### 4.8 LLM 调用成本参考

根据官方论文：RD-Agent(Q) 完成一次完整的量化 R&D 循环（含因子挖掘 + 模型优化），**成本低于 $10**（使用 GPT-4o）。

---

## 5. RD-Agent 可扩展性

### 5.1 模块化架构

RD-Agent 采用清晰的分层架构：

```
rdagent/
├── core/              # 核心抽象框架（不可直接使用）
│   ├── proposal/      # 假设生成、实验规划、反馈
│   ├── developer/     # 代码生成器（CoSTEER）
│   └── ...
├── components/        # 可复用组件
│   ├── coder/         # 代码生成组件
│   │   ├── factor_coder/
│   │   ├── model_coder/
│   │   └── data_science/
│   ├── runner/        # 执行器组件
│   └── ...
├── scenarios/         # 具体场景实现
│   ├── qlib/          # 量化金融（Qlib）
│   │   ├── proposal/  # 假设生成策略
│   │   ├── developer/ # 因子/模型开发
│   │   ├── experiment/# 实验环境
│   │   └── prompts.yaml
│   ├── data_science/  # 数据科学
│   ├── kaggle/        # Kaggle 竞赛
│   ├── finetune/      # LLM 微调
│   ├── general_model/ # 通用模型
│   └── rl/            # 强化学习
├── app/               # 应用入口（CLI 命令）
│   ├── qlib_rd_loop/  # 量化 R&D 循环
│   ├── data_science/
│   ├── kaggle/
│   ├── finetune/
│   ├── benchmark/
│   └── cli.py         # CLI 入口
└── utils/             # 工具函数
```

### 5.2 组件替换机制

RD-Agent 的配置采用**字符串类路径**引用所有组件，这意味着你可以通过 `.env` 或环境变量替换任意组件：

```bash
# .env 示例：替换因子假设生成器
QLIB_QUANT_factor_hypothesis_gen=my_package.MyFactorHypothesisGen
QLIB_QUANT_factor_coder=my_package.MyFactorCoSTEER
QLIB_QUANT_factor_runner=my_package.MyFactorRunner
QLIB_QUANT_factor_summarizer=my_package.MyFeedbackGenerator

# 控制迭代行为
QLIB_QUANT_evolving_n=20               # 迭代轮数（默认10）
QLIB_QUANT_action_selection=bandit      # 动作选择策略：bandit|llm|random
```

**所有可替换的组件类路径**（来自 `QuantBasePropSetting`）：

| 组件 | 环境变量前缀 | 默认类 |
|------|-------------|--------|
| 场景 | `QLIB_QUANT_scen` | `QlibQuantScenario` |
| 假设生成 | `QLIB_QUANT_quant_hypothesis_gen` | `QlibQuantHypothesisGen` |
| 因子转实验 | `QLIB_QUANT_factor_hypothesis2experiment` | `QlibFactorHypothesis2Experiment` |
| 因子编码器 | `QLIB_QUANT_factor_coder` | `QlibFactorCoSTEER` |
| 因子运行器 | `QLIB_QUANT_factor_runner` | `QlibFactorRunner` |
| 因子总结器 | `QLIB_QUANT_factor_summarizer` | `QlibFactorExperiment2Feedback` |
| 模型转实验 | `QLIB_QUANT_model_hypothesis2experiment` | `QlibModelHypothesis2Experiment` |
| 模型编码器 | `QLIB_QUANT_model_coder` | `QlibModelCoSTEER` |
| 模型运行器 | `QLIB_QUANT_model_runner` | `QlibModelRunner` |
| 模型总结器 | `QLIB_QUANT_model_summarizer` | `QlibModelExperiment2Feedback` |

### 5.3 自定义场景开发

添加全新场景的步骤：

1. **创建场景类**：继承 `rdagent.core.scenario.ASpecificScen`
2. **实现假设生成器**：继承 `HypothesisGen`，实现 `gen(trace) → Hypothesis`
3. **实现实验转换器**：继承 `Hypothesis2Experiment`，实现 `convert()`
4. **实现编码器**：继承 CoSTEER 系列或自定义 `Developer`
5. **实现运行器**：继承 `Runner`，定义 Docker/Conda 执行环境
6. **实现反馈器**：继承 `Experiment2Feedback`，实现 `generate_feedback()`
7. **注册 App**：在 `rdagent/app/` 下创建入口脚本

### 5.4 因子实验加载器

RD-Agent 提供了 `rdagent/scenarios/qlib/factor_experiment_loader/` 模块，用于加载和管理历史因子实验，便于复现和增量开发。

### 5.5 时间段自定义

```bash
# 因子场景时间段配置
QLIB_QUANT_TRAIN_START=2008-01-01
QLIB_QUANT_TRAIN_END=2014-12-31
QLIB_QUANT_VALID_START=2015-01-01
QLIB_QUANT_VALID_END=2016-12-31
QLIB_QUANT_TEST_START=2017-01-01
QLIB_QUANT_TEST_END=2020-08-01
```

### 5.6 知识库扩展

支持自定义知识库和知识库路径：
```bash
QLIB_QUANT_knowledge_base=rdagent.scenarios.qlib.knowledge.MyKnowledgeBase
QLIB_QUANT_knowledge_base_path=/path/to/custom_kb
```

---

## 6. 编排集成建议

### 6.1 推荐集成架构

```
┌─────────────────────────────────────────────┐
│           编排平台 (Orchestrator)            │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌────────────┐  │
│  │ Scheduler│  │ Monitor │  │ Results DB │  │
│  └────┬────┘  └────┬────┘  └──────┬─────┘  │
│       │            │              │         │
│       ▼            ▼              ▼         │
│  ┌──────────────────────────────────────┐   │
│  │     RD-Agent Wrapper Service         │   │
│  │  ┌─────────────────────────────────┐ │   │
│  │  │ subprocess: rdagent fin_quant   │ │   │
│  │  │ + .env configuration            │ │   │
│  │  └─────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────┐ │   │
│  │  │ Log Parser (日志解析器)         │ │   │
│  │  │ → 提取因子代码/指标/反馈       │ │   │
│  │  └─────────────────────────────────┘ │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  RD-Agent 进程    │
         │  (Docker + Qlib)  │
         └──────────────────┘
```

### 6.2 集成步骤

1. **环境准备**：在专用 Linux 机器/容器上安装 RD-Agent
2. **LLM 配置**：在 `.env` 中配置 DeepSeek 或其他 LLM
3. **封装层开发**：
   - 使用 Python `subprocess` 调用 `rdagent fin_quant`
   - 监控 `log/` 目录变化
   - 解析 trace.pkl 和 JSON 日志
   - 提取因子代码和回测指标
4. **调度策略**：
   - 按需触发（事件驱动）
   - 定时触发（每日/每周收盘后运行）
   - 增量运行（从指定 checkpoint 恢复）
5. **结果处理**：
   - 因子代码提取 → 导入 Qlib 策略库
   - 回测指标 → 写入数据库
   - Trace 分析 → 生成研究报告

### 6.3 已知限制

| 限制 | 影响 | 缓解方案 |
|------|------|----------|
| 仅支持 Linux | 部署平台受限 | 使用 Docker 部署 |
| 无 REST API | 无法直接 HTTP 调用 | 自行封装 Flask/FastAPI |
| 输出为日志文件 | 结构化解析困难 | 编写日志解析器 |
| Trace 用 pickle | 跨语言不兼容 | 仅用 Python 编排 |
| 单进程运行 | 无法并行多场景 | 多容器隔离部署 |
| LLM 依赖 | 需要 API key 和网络 | 使用本地 LLM（vLLM + LiteLLM） |

### 6.4 与现有量化基础设施的整合路径

```
RD-Agent 产出          →  整合目标
────────────────────────────────────
因子 .py 代码           →  Qlib 因子库 / 自研因子仓库
模型配置 + 训练脚本      →  Qlib 模型库 / 模型注册表
回测指标 (IC/ARR/Sharpe) →  绩效数据库 / Grafana 面板
Trace (R&D 轨迹)       →  研究知识库 / 决策审计日志
假设 + 反馈记录          →  研报自动生成 / 策略归因
```

---

## 附录

### A. 关键源码路径

| 路径 | 说明 |
|------|------|
| `rdagent/app/cli.py` | CLI 入口（所有 `rdagent` 命令定义） |
| `rdagent/app/qlib_rd_loop/conf.py` | 量化场景配置（Pydantic Settings） |
| `rdagent/app/qlib_rd_loop/factor.py` | 因子挖掘循环入口 |
| `rdagent/app/qlib_rd_loop/quant.py` | 量化联合循环入口 |
| `rdagent/scenarios/qlib/proposal/` | 假设生成策略 |
| `rdagent/scenarios/qlib/developer/` | 因子/模型开发实现 |
| `rdagent/scenarios/qlib/experiment/` | 实验环境定义 |
| `rdagent/core/proposal.py` | 核心 R&D 循环抽象类 |

### B. 参考文献

- [RD-Agent GitHub](https://github.com/microsoft/RD-Agent)
- [RD-Agent 文档](https://rdagent.readthedocs.io/)
- [RD-Agent 技术报告](https://arxiv.org/abs/2505.14738)
- [RD-Agent-Quant 论文 (NeurIPS 2025)](https://arxiv.org/abs/2505.15155)
- [LiteLLM 文档](https://docs.litellm.ai/docs)
- 版本：v0.8.0 (2026年8月)
