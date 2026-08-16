# RD-Agent 量化场景与部署调研报告

> 调研时间：2026-08-10  
> 来源：GitHub microsoft/RD-Agent 官方仓库、ReadtheDocs 文档、arXiv 论文 (2505.15155, 2505.14738)、PyPI 页面

---

## 主题一：RD-Agent 因子挖掘与量化场景

### 1.1 总体定位

RD-Agent(Q)（R&D-Agent for Quantitative Finance）是**首个以数据为中心的多智能体量化研究框架**，由微软研究院 MIIC 团队开发，发表于 NeurIPS 2025。其核心目标是自动化量化策略的全栈研发流程，通过**因子-模型协同优化**（factor-model co-optimization）实现策略的迭代进化。

根据 arXiv:2505.15155 论文，RD-Agent(Q) 在真实A股市场实验中，以**不到 $10 的 LLM API 成本**，使用比基准因子库少 70% 以上的因子，实现了约 **2 倍的年化超额收益率（ARR）**，并超越了当时最先进的深度时序模型。

### 1.2 三大量化运行模式

RD-Agent 的 Qlib 场景提供三个独立的 CLI 命令，对应三种运行模式：

| 命令 | 模式 | 说明 |
|------|------|------|
| `rdagent fin_factor` | 因子挖掘循环 | 自动提出因子假设→编写因子代码→回测→反馈→改进 |
| `rdagent fin_model` | 模型优化循环 | 自动提出模型假设→编写模型代码→回测→反馈→改进 |
| `rdagent fin_quant` | 因子+模型联合循环 | 交替进行因子优化和模型优化（完整 RD-Agent(Q)） |

此外还有 `rdagent fin_factor_report`，从财报 PDF 中自动提取因子并实现。

### 1.3 因子挖掘循环（Factor Mining Loop）详细流程

因子挖掘循环包含 6 个步骤，形成闭环：

**Step 1：假设生成（Hypothesis Generation）🔍**
- 由 `QlibFactorHypothesisGen` 类驱动
- 基于先前实验分析、领域专业知识生成初始假设
- 每个假设包含金融逻辑推理和依据

**Step 2：因子创建（Factor Creation）✨**
- 由 `QlibFactorHypothesis2Experiment` 类将假设转化为具体任务
- 每个任务包含：因子名称、描述、公式定义、变量说明
- 将假设拆分为多个可执行的因子开发子任务

**Step 3：因子代码实现（Factor Implementation）👨‍💻**
- 由 `QlibFactorCoSTEER`（Co-STEER 系统）负责代码生成
- Co-STEER 是 RD-Agent 的核心代码生成引擎，采用**迭代进化**方式：
  - **max_loop**: 最多 10 次实现循环（可配置）
  - **fail_task_trial_limit**: 失败任务最多重试 20 次
  - 支持 v1/v2 两种查询策略，可从知识库中检索历史成功/失败经验
  - `knowledge_base_path` 和 `new_knowledge_base_path` 管理知识库
  - `coder_use_cache` 控制是否使用缓存
  - `file_based_execution_timeout`: 每个因子执行超时默认 3600 秒
- 生成的因子代码基于 Python + Pandas/Numpy，与 Qlib 框架兼容

**Step 4：回测（Backtesting with Qlib）📉**
- 由 `QlibFactorRunner` 类执行
- 将因子集成到 Qlib 的 Alpha158 基础因子库中
- 使用 LGBModel（LightGBM）进行训练和评估
- 数据集：CSI300（沪深300成分股）
- 默认数据分段：
  - 训练集：2008-01-01 至 2014-12-31
  - 验证集：2015-01-01 至 2016-12-31
  - 测试集（回测）：2017-01-01 至 2020-08-01
- 回测配置：
  - 策略：TopkDropoutStrategy（选 Top 50 股票，随机丢弃 5 只引入探索）
  - 初始资金：1 亿（100,000,000）
  - 包含开盘/收盘交易成本、最小交易成本、滑点控制
  - 基准：SH000300（沪深300指数）

**Step 5：反馈分析（Feedback Analysis）🔍**
- 由 `QlibFactorExperiment2Feedback` 类负责
- 分析回测结果，评估因子有效性
- 生成结构化反馈供下一轮迭代使用

**Step 6：假设改进（Hypothesis Refinement）♻️**
- 基于反馈精炼假设
- 循环回到 Step 1，持续改进
- 默认迭代次数 `evolving_n = 10`

### 1.4 模型优化循环（Model Tuning Loop）

模型优化循环结构与因子循环类似，但关注点不同：

- **假设生成**：`QlibModelHypothesisGen` — 提出模型结构假设（如 RNN、Attention 等）
- **假设转实验**：`QlibModelHypothesis2Experiment`
- **代码实现**：`QlibModelCoSTEER` — 生成 PyTorch 模型代码
- **执行回测**：`QlibModelRunner` — 使用 Alpha158 的 20 个因子和新生成的模型在 Qlib 中回测
- **反馈**：`QlibModelExperiment2Feedback`

模型场景的默认超参数：
- n_epochs: 100，lr: 1e-3，early_stop: 10
- batch_size: 2000，loss: mse，metric: loss
- n_jobs: 20（并行任务数）
- GPU: 0（使用 GPU 0 如果可用）

### 1.5 因子+模型联合优化（Fin-Quant）

`rdagent fin_quant` 是完整的 RD-Agent(Q) 模式，核心创新在于：

- **多臂赌博机调度器（Multi-Armed Bandit Scheduler）**：用于自适应选择下一步是优化因子还是模型
  - `action_selection` 配置项支持三种策略：`bandit`（默认）、`llm`（LLM 选择）、`random`（随机）
- **交替优化**：因子和模型交替迭代，每次选择当前最有可能提升的方向
- **知识共享**：因子和模型优化的经验都存储在共享知识库中

### 1.6 因子代码生成与筛选机制

**代码生成（Co-STEER 系统）**：
- Co-STEER = Collaborative Evolving Strategy
- 核心思想：像人类开发者一样迭代进化代码
- 工作流程：
  1. 接收因子/模型的设计描述
  2. 查询知识库获取相关历史经验（成功案例、失败教训）
  3. LLM 生成初始代码
  4. 在 Docker/Conda 环境中执行测试
  5. 如果失败，分析错误→查询类似成功案例→重新生成
  6. 循环直到代码可运行或达到 max_loop 上限

**因子筛选**：
- 因子执行后生成 `combined_factors_df.parquet` 文件
- 通过 Qlib 的回测管线评估因子表现
- `select_method` 配置项（默认 `random`）控制因子选择策略
- 回测指标包括：IC（信息系数）、IR（信息比率）、年化收益率、夏普比率等
- 反馈系统会综合考虑这些指标决定因子的保留/淘汰

### 1.7 回测结果格式

RD-Agent 依赖 Qlib 的回测体系，结果通过以下 Record 组件记录：

- **SignalRecord**：记录模型预测信号
- **SigAnaRecord**：信号分析（IC、ICIR、Rank IC 等），不做多空分离
- **PortAnaRecord**：组合分析，包含回测的收益曲线、超额收益、夏普比率、最大回撤等

结果数据以 MLflow 格式存储（RD-Agent 集成了 mlflow 和 azureml-mlflow），可通过 Streamlit UI 或 Web UI 可视化查看。

### 1.8 因子库管理方式

- **数据格式**：因子数据以 Parquet 文件格式存储（`combined_factors_df.parquet`）
- **因子源数据路径**：`git_ignore_folder/factor_implementation_source_data`（可通过 `FACTOR_CoSTEER_data_folder` 环境变量配置）
- **知识库**：
  - `knowledge_base_path`：已有知识库路径
  - `new_knowledge_base_path`：新生成的知识库路径
  - 知识库存储因子实现的经验（成功模式、常见错误等）
  - 使用向量嵌入（Embedding）进行语义检索
- **Qlib 数据**：存储在 `~/.qlib/qlib_data/cn_data`，包含股票行情数据
- **Qlib 配置**：YAML 文件位于 `model_template` 和 `factor_template` 目录中

### 1.9 代码结构（rdagent/scenarios/qlib）

根据 pyproject.toml 和文档，代码组织如下：

```
rdagent/
├── core/                    # 核心抽象框架
├── components/              # 通用组件
│   ├── coder/
│   │   ├── factor_coder/    # 因子代码生成器基类和配置
│   │   └── model_coder/     # 模型代码生成器基类和配置
│   └── ...
├── scenarios/qlib/          # Qlib 量化场景
│   ├── experiment/          # 实验定义
│   │   ├── factor_experiment.py
│   │   ├── model_experiment.py
│   │   └── quant_experiment.py
│   ├── proposal/            # 假设生成
│   │   ├── factor_proposal.py
│   │   ├── model_proposal.py
│   │   └── quant_proposal.py
│   ├── developer/           # 代码实现与执行
│   │   ├── factor_coder.py  # QlibFactorCoSTEER
│   │   ├── factor_runner.py # QlibFactorRunner
│   │   ├── model_coder.py   # QlibModelCoSTEER
│   │   ├── model_runner.py  # QlibModelRunner
│   │   └── feedback.py      # 反馈分析
│   └── ...
├── app/                     # CLI 应用入口
│   ├── qlib_rd_loop/        # Qlib R&D 循环
│   │   └── conf.py          # 环境配置定义
│   └── cli.py               # Typer CLI 入口
```

---

## 主题二：RD-Agent 部署与资源需求

### 2.1 系统要求

**重要限制：RD-Agent 目前仅支持 Linux 系统。** CI 测试平台为 Linux，不支持 macOS 和 Windows（Docker 内执行代码的场景也依赖 Linux 容器）。

### 2.2 Python 环境要求

- **Python 版本**：要求 >= 3.10，CI 中充分测试的版本为 **3.10 和 3.11**
- **包管理**：推荐使用 Conda 环境隔离

```bash
conda create -n rdagent python=3.10
conda activate rdagent
```

### 2.3 安装方式

**用户安装（PyPI）**：
```bash
pip install rdagent
```

**开发者安装（源码）**：
```bash
git clone https://github.com/microsoft/RD-Agent
cd RD-Agent
make dev
```

**可选依赖**：
- `pip install rdagent[torch]` — 安装 PyTorch（部分 Agent 算法需要）
- `pip install rdagent[test]` — 测试依赖
- `pip install rdagent[docs]` — 文档构建
- `pip install rdagent[lint]` — 代码检查

### 2.4 核心依赖包

根据 `requirements.txt`，主要依赖包括：

| 类别 | 包 | 用途 |
|------|------|------|
| LLM 交互 | `litellm>=1.73`, `openai`, `langchain`, `langchain-community` | 多 LLM 提供商接入 |
| Agent 框架 | `pydantic-ai-slim[mcp,openai,prefect]==1.66.0`, `nest-asyncio` | Agent 编排 |
| 数据处理 | `numpy`, `pandas`, `pyarrow`, `scikit-learn`, `tables` | 因子计算与数据处理 |
| 可视化 | `streamlit>=1.47`, `plotly`, `matplotlib`, `seaborn` | UI 与图表 |
| Web UI | `flask`, `flask-cors`, `networkx` | 新版 Web 前端后端 |
| PDF 处理 | `pymupdf`, `pypdf`, `azure-ai-formrecognizer` | 财报提取 |
| 代码分析 | `tree-sitter`, `tree-sitter-python` | 代码解析与修复 |
| Docker 交互 | `docker` | 代码在容器中执行 |
| ML 追踪 | `mlflow`, `azureml-mlflow` | 实验追踪 |
| 搜索/爬虫 | `selenium`, `webdriver-manager`, `duckduckgo-search` | 网页搜索与爬取 |
| 配置管理 | `pydantic-settings`, `python-dotenv` | 环境配置 |
| 其他 | `loguru`, `rich`, `tqdm`, `typer`, `tiktoken` | 日志、CLI、进度 |

**PyTorch 是可选的**，仅当使用 `pip install rdagent[torch]` 时安装。部分模型训练场景（如 Qlib 的神经网络模型）可能需要。

### 2.5 Docker 镜像配置

**Docker 是核心依赖**。RD-Agent 的 Co-STEER 代码生成系统在 Docker 容器中执行因子/模型代码，确保隔离和可复现性。

要求：
- 安装 Docker Engine（参考[官方文档](https://docs.docker.com/engine/install/)）
- **当前用户必须能免 sudo 运行 Docker 命令**
- 验证方式：`docker run hello-world` 成功即可

执行环境配置（`.env` 文件）：
- **模型场景**：`MODEL_COSTEER_ENV_TYPE=docker`（推荐）或 `conda`（本地环境）
- **数据科学场景**：`DS_CODER_COSTEER_ENV_TYPE=docker`（推荐）或 `conda`

RD-Agent 会自动构建和使用包含 Qlib + 必要依赖的 Docker 镜像。代码执行时，因子/模型代码被注入容器中运行，结果传回主进程。

### 2.6 LLM 配置（必需）

RD-Agent 的运行**必须配置 LLM 后端**，需要两种能力：
1. **ChatCompletion**（对话补全）— 核心推理
2. **Embedding**（向量嵌入）— 知识库语义检索

默认使用 **LiteLLM** 作为统一后端，支持：

**Option 1：统一 API（如 OpenAI）**
```env
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_BASE=<api_base>
OPENAI_API_KEY=<api_key>
```

**Option 2：分离 API（如 Chat 用 DeepSeek，Embedding 用 SiliconFlow）**
```env
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=<key>
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=<key>
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
```

**注意**：使用推理模型（如 DeepSeek-R1 等包含 `<think>` 标签的模型）需要额外设置 `REASONING_THINK_RM=True`。

健康检查命令验证配置：
```bash
rdagent health_check
```

### 2.7 CPU / 内存 / 磁盘资源消耗

**CPU**：
- RD-Agent 主进程本身是 I/O 密集型（等待 LLM API 响应），CPU 消耗低
- 但 Docker 容器内的 Qlib 回测是 CPU 密集型任务
- Qlib 配置默认 `n_jobs: 20`（20 个并行任务），实际并行度取决于 CPU 核心数
- **推荐**：至少 4 核 CPU，8 核以上更佳（尤其并行回测场景）

**内存**：
- 主进程 + Streamlit UI 约需 1-2 GB
- Docker 容器中的 Qlib 回测需加载 A 股数据，内存消耗较大
- **推荐**：至少 16 GB RAM，32 GB 更为安全

**磁盘**：
- RD-Agent 包及依赖：约 2-3 GB
- Docker 镜像：约 5-10 GB（包含 Qlib、Python 环境、依赖库）
- Qlib 中国市场数据（`~/.qlib/qlib_data/cn_data`）：约 2-3 GB
- 因子源数据、实验日志、知识库：约 1-5 GB（随使用增长）
- MLflow 实验记录：随迭代次数线性增长
- **推荐**：至少 50 GB 可用磁盘空间

### 2.8 是否需要 GPU

**RD-Agent 框架本身不需要 GPU**。

Qlib 的因子挖掘场景使用 LGBModel（LightGBM），**不需要 GPU**。

以下场景**可选使用 GPU**：
- 模型优化场景中，如果生成的模型是 PyTorch 神经网络（如 GeneralPTNN），GPU 可加速训练
- Qlib YAML 配置中默认 `GPU: 0`（使用 GPU 0），但也可设为 `-1` 使用 CPU
- 数据科学场景中的深度学习模型训练

**结论**：GPU 非必需，但模型优化场景有 GPU 更快。无 GPU 时模型训练自动回退到 CPU。

### 2.9 数据存储格式

RD-Agent 的数据存储采用**文件系统 + MLflow**的方式，不使用传统数据库：

| 数据类型 | 存储方式 | 路径 |
|----------|----------|------|
| Qlib 行情数据 | Qlib 二进制格式 | `~/.qlib/qlib_data/cn_data/` |
| 因子计算结果 | Parquet 文件 | `combined_factors_df.parquet` |
| 因子源数据 | 文件系统 | `git_ignore_folder/factor_implementation_source_data/` |
| 实验日志/指标 | MLflow | 本地文件系统或 Azure ML |
| 知识库 | 向量嵌入 + JSON/文件 | 可配置路径 |
| 运行配置 | YAML（Qlib） + `.env`（RD-Agent） | 各 template 目录 |
| 应用日志 | 文件系统 | `log/` 目录 |

**不使用 SQLite**。所有状态和结果通过文件系统和 MLflow 管理。Parquet 是因子数据的标准格式，确保高效的列式存储和读取。

### 2.10 常见安装问题与解决方案

**1. Docker 权限问题**
```
Error: permission denied while trying to connect to the Docker daemon
```
解决：将用户加入 docker 组：`sudo usermod -aG docker $USER`，然后重新登录。

**2. Python 版本不兼容**
- RD-Agent 要求 Python >= 3.10，3.10/3.11 最佳
- Python 3.12+ 可能存在部分依赖不兼容

**3. LLM API 配置错误**
- 使用 `rdagent health_check` 验证配置
- 确认 `CHAT_MODEL` 和 `EMBEDDING_MODEL` 名称符合 LiteLLM 规范
- 不同提供商的模型需要对应的 API Key 环境变量
- Embedding 模型来自不同提供商时，必须添加 `litellm_proxy/` 前缀

**4. 端口 19899 被占用**
- UI 默认端口 19899
- 检查：`rdagent health_check --no-check-env --no-check-docker`
- 解决：`rdagent ui --port <其他端口>` 或 `rdagent server_ui --port <其他端口>`

**5. 网络连接问题**
- Qlib 数据下载需要访问微软 CDN
- 部分 Python 包（如 `azure-ai-formrecognizer`）需要 pip 安装
- 国内用户可能需要配置 pip 镜像源和 Docker 镜像加速

**6. Conda 与 Docker 执行环境冲突**
- 默认推荐 Docker 模式（`*_ENV_TYPE=docker`）
- 如遇 Docker 资源限制，可切换到 Conda 模式（`*_ENV_TYPE=conda`）
- Conda 模式要求本地环境已安装 Qlib 及所有依赖

**7. DeepSeek 模型配置错误**
- 这是常见问题。完整配置示例：
  - `CHAT_MODEL=deepseek/deepseek-chat`（注意 `deepseek/` 前缀）
  - `DEEPSEEK_API_KEY` 设置正确
  - Embedding 使用其他提供商（如 SiliconFlow），需添加 `litellm_proxy/` 前缀

**8. 推理模型响应解析失败**
- 如果 LLM 响应包含 `<think>` 标签（如 DeepSeek-R1）
- 设置 `REASONING_THINK_RM=True` 以过滤思维链内容

### 2.11 健康检查

RD-Agent 提供内置健康检查工具：

```bash
# 完整检查（Docker + 环境 + 端口）
rdagent health_check

# 仅检查 Docker（不验证 LLM 配置）
rdagent health_check --no-check-env

# 仅检查端口占用
rdagent health_check --no-check-env --no-check-docker
```

### 2.12 UI 与监控

RD-Agent 提供两种 UI：

**Streamlit UI**（传统）：
```bash
rdagent ui --port 19899 --log-dir <log_folder>
```
- 支持 `--data-science` 标志切换数据科学场景视图
- 适合查看运行日志和因子/模型迭代详情

**Web UI**（新版 Flask + 前端）：
```bash
cd web && npm install && npm run build:flask
rdagent server_ui --port 19899
```
- 实时交互和 trace 查看
- 目前不支持 `data_science` 场景

### 2.13 时间分段自定义配置

通过 `.env` 环境变量可自定义训练/验证/测试时间窗口：

- **Fin-Factor**：`QLIB_FACTOR_TRAIN_START`, `QLIB_FACTOR_TRAIN_END`, `QLIB_FACTOR_VALID_START`, `QLIB_FACTOR_VALID_END`, `QLIB_FACTOR_TEST_START`, `QLIB_FACTOR_TEST_END`
- **Fin-Model**：对应 `QLIB_MODEL_*` 前缀
- **Fin-Quant**：同时支持 `QLIB_FACTOR_*`、`QLIB_MODEL_*`、`QLIB_QUANT_*`（后者仅用于前端显示）

---

## 总结

RD-Agent 是一个成熟的 AI 驱动量化研究自动化框架，具有以下特点：

1. **量化能力**：完整的因子挖掘→回测→反馈闭环，支持因子-模型联合优化，在真实市场验证中表现优异
2. **部署门槛**：需要 Linux + Docker + LLM API，Python 3.10/3.11 环境，安装相对简单（`pip install rdagent`）
3. **资源需求**：CPU 4-8+ 核，内存 16-32 GB，磁盘 50+ GB；GPU 可选非必需
4. **成本极低**：一次完整因子-模型迭代实验的 LLM API 成本可控制在 $10 以内
5. **数据架构**：基于文件系统 + Parquet + MLflow，无数据库依赖
6. **LLM 后端**：通过 LiteLLM 支持多种模型（OpenAI、DeepSeek、Azure 等），配置灵活
