# 微软 RD-Agent 技术架构深度调研报告

> **仓库地址**：https://github.com/microsoft/RD-Agent  
> **技术报告**：https://aka.ms/RD-Agent-Tech-Report (arXiv: 2505.14738)  
> **调研日期**：2026-08-10  
> **PyPI 包名**：`rdagent`  
> **许可协议**：MIT  

---

## 一、项目概述

RD-Agent（原名 R&D-Agent）是微软亚洲研究院（MSRA-MIIC）开发的一个**自动化研发智能体框架**。其核心理念是将工业界最有价值的 R&D 流程自动化——用 "R"（Research Agent）提出新想法/假设，用 "D"（Development Agent）实现这些想法，通过不断迭代进化来产出有工业价值的解决方案。

项目当前聚焦于**数据驱动场景**，主要应用领域包括：

| 场景 | CLI 命令 | 说明 |
|------|----------|------|
| 量化因子迭代 | `rdagent fin_factor` | 基于 Qlib 的因子自动提出-实现-评估循环 |
| 量化模型迭代 | `rdagent fin_model` | 基于 Qlib 的模型结构自动进化 |
| 量化全流水线 | `rdagent fin_quant` | 因子+模型联合优化（RD-Agent(Q)） |
| 金融报告因子提取 | `rdagent fin_factor_report` | 从财报中提取因子并实现 |
| 论文模型复现 | `rdagent general_model <URL>` | 自动读取论文并实现模型 |
| 数据科学/Kaggle | `rdagent data_science --competition <name>` | MLE-bench / Kaggle 竞赛自动化 |
| LLM 微调 | `rdagent llm_finetune` | FT-Agent：自主微调 LLM |

**关键成就**：
- MLE-bench 排行榜第一（30.22% 总体成功率），超越 AIDE
- RD-Agent(Q) 以 <$10 成本实现 ~2x ARR，因子数量减少 70%+
- NeurIPS 2025 / ICML 2026 / ACL 2026 论文接收

---

## 二、核心组件架构

### 2.1 整体分层架构

RD-Agent 的代码结构位于 `rdagent/` 包下，采用清晰的分层设计：

```
rdagent/
├── app/              # 应用入口层（CLI、各场景的循环入口）
│   ├── cli.py        # Typer CLI 总入口
│   ├── qlib_rd_loop/ # Qlib 量化场景（factor/model/quant/factor_from_report）
│   ├── data_science/ # 数据科学场景（Kaggle/MLE-bench）
│   ├── finetune/     # LLM 微调场景
│   ├── general_model/# 通用模型复现场景
│   └── benchmark/    # 基准测试工具
├── core/             # 核心抽象层
│   ├── experiment.py # Experiment/Task/Workspace 核心数据模型
│   ├── proposal.py   # Hypothesis/Trace/Feedback 提案系统
│   ├── developer.py  # Developer 接口
│   ├── evaluation.py # Feedback 抽象
│   ├── scenario.py   # Scenario 抽象
│   └── conf.py       # 全局配置 (RD_AGENT_SETTINGS)
├── components/       # 可复用组件层
│   ├── workflow/     # RDLoop 核心循环引擎
│   ├── coder/        # 代码生成器（CoSTEER 框架）
│   │   ├── factor_coder/   # 因子代码生成
│   │   ├── model_coder/    # 模型代码生成
│   │   └── data_science/   # 数据科学代码生成
│   ├── evaluator/    # 评估器
│   ├── extractor/    # 信息提取器
│   └── runner/       # 运行器（执行代码）
├── scenarios/        # 场景定义层
│   ├── qlib/         # Qlib 量化场景完整实现
│   └── ...
├── oai/              # LLM 后端抽象层
│   ├── backend/      # API 后端（LiteLLM / Deprecated）
│   ├── llm_utils.py  # LLM 工具函数
│   └── llm_conf.py   # LLM 配置
├── utils/            # 工具层
│   ├── env.py        # Docker/Conda 环境管理
│   ├── workflow.py   # LoopBase/LoopMeta 循环框架
│   └── qlib.py       # Qlib 工具函数
└── log/              # 日志与 UI 层
    ├── ui/           # Streamlit Web UI
    ├── server/       # Flask 实时服务器
    └── storage.py    # 日志存储
```

### 2.2 核心数据模型（rdagent/core/experiment.py）

这是整个框架的基础数据结构：

**Task（任务）**：表示一个待执行的工作单元，包含名称、描述、用户指令等。

**Workspace（工作空间）**：代码实现的工作目录。核心子类 `FBWorkspace`（File-Based Workspace）实现了：
- `file_dict`：存储注入的代码文件（字典形式）
- `workspace_path`：实际文件系统路径（UUID 命名，位于配置的 workspace_path 下）
- `inject_files(**files)`：注入/删除代码文件（`__DEL__` 表示删除）
- `execute(env, entry)`：在指定环境中执行代码
- `create_ws_ckp()` / `recover_ws_ckp()`：内存级检查点（zip 压缩），支持回滚

**Experiment（实验）**：一次完整的实验记录，包含：
- `sub_tasks`：子任务序列
- `sub_workspace_list`：每个子任务对应的 Workspace
- `hypothesis`：生成该实验的假设
- `based_experiments`：基于的历史实验
- `experiment_workspace`：整体实验工作空间
- `running_info`：运行结果
- `plan`：实验计划（ExperimentPlan，字典类型）

### 2.3 提案与追踪系统（rdagent/core/proposal.py）

**Hypothesis（假设）**：Research Agent 的产出，包含：
- `hypothesis`：假设文本
- `reason`：推理过程
- `concise_reason / concise_observation / concise_justification / concise_knowledge`：精简描述

**Trace（追踪）**：维护实验历史的 **DAG（有向无环图）** 结构：
- `hist`：`(Experiment, Feedback)` 元组列表
- `dag_parent`：每个节点的父节点索引
- `current_selection`：当前展开点（默认 `SEL_LATEST_SOTA = (-1,)`）
- 支持 `get_sota_experiment()`：沿祖先链回溯找到最优实验
- 支持 `get_parent_exps()` / `get_children()`：遍历实验谱系

**关键抽象类**：
- `HypothesisGen`：根据 Trace 生成新假设
- `Hypothesis2Experiment`：将假设转化为可执行的 Experiment
- `Experiment2Feedback`（Summarizer）：根据实验结果生成反馈
- `ExpPlanner`：实验规划器
- `CheckpointSelector`：检查点选择策略

### 2.4 RDLoop 循环引擎（rdagent/components/workflow/rd_loop.py）

`RDLoop` 是所有场景共享的核心循环引擎，继承自 `LoopBase`（使用 `LoopMeta` 元类实现步骤注册）。

**初始化**：通过 `PROP_SETTING`（`BasePropSetting` 子类）动态导入各组件：
```python
class RDLoop(LoopBase, metaclass=LoopMeta):
    def __init__(self, PROP_SETTING):
        scen = import_class(PROP_SETTING.scen)()        # 场景
        self.hypothesis_gen = import_class(PROP_SETTING.hypothesis_gen)(scen)
        self.hypothesis2experiment = import_class(PROP_SETTING.hypothesis2experiment)()
        self.coder = import_class(PROP_SETTING.coder)(scen)        # 代码生成器
        self.runner = import_class(PROP_SETTING.runner)(scen)      # 运行器
        self.summarizer = import_class(PROP_SETTING.summarizer)(scen)  # 反馈生成器
        self.trace = Trace(scen=scen)
```

**循环步骤**（每一步的输出作为下一步的输入）：

| 步骤 | 方法 | 说明 |
|------|------|------|
| 1. `direct_exp_gen` | 提出假设 → 生成实验 | 调用 `hypothesis_gen.gen()` 和 `hypothesis2experiment.convert()` |
| 2. `coding` | 代码实现 | 调用 `coder.develop(exp)` 生成代码 |
| 3. `running` | 运行实验 | 调用 `runner.develop(exp)` 在 Docker 中执行 |
| 4. `feedback` | 反馈生成 | 调用 `summarizer.generate_feedback()` |
| 5. `record` | 记录到 Trace | `trace.sync_dag_parent_and_hist()` |

循环支持：
- **并行多轨迹**：`get_max_parallel()` 控制并行度
- **用户交互**：通过 multiprocessing.Queue 实现人在回路（hypothesis/feature 选择）
- **异常恢复**：`skip_loop_error` 机制跳过失败循环
- **会话保存/加载**：`FactorRDLoop.load(path)` 恢复历史会话

### 2.5 BasePropSetting 配置（rdagent/components/workflow/conf.py）

每个场景通过 `BasePropSetting` 子类定义循环的组件配置：

```python
class BasePropSetting(ExtendedBaseSettings):
    scen: str | None = None              # 场景类路径
    hypothesis_gen: str | None = None    # 假设生成器类路径
    hypothesis2experiment: str | None = None  # 假设→实验转换器
    coder: str | None = None             # 代码生成器
    runner: str | None = None            # 运行器
    summarizer: str | None = None        # 反馈生成器
    evolving_n: int = 10                 # 进化次数
```

所有组件通过**字符串类路径**配置，运行时使用 `import_class()` 动态导入，实现了高度解耦。

---

## 三、LLM 调用链路

### 3.1 LLM 后端架构（rdagent/oai/）

**配置层**（`llm_conf.py`）：
```python
class LLMSettings(ExtendedBaseSettings):
    backend: str = "rdagent.oai.backend.LiteLLMAPIBackend"
    chat_model: str = "gpt-4-turbo"
    embedding_model: str = "text-embedding-3-small"
    chat_temperature: float = 0.5
    chat_max_tokens: int | None = None
    chat_stream: bool = True
    max_past_message_include: int = 10
    max_retry: int = 10
    # ...更多参数
```

**后端获取**（`llm_utils.py`）：
```python
def get_api_backend(*args, **kwargs) -> BaseAPIBackend:
    api_backend_cls = import_class(LLM_SETTINGS.backend)
    return api_backend_cls(*args, **kwargs)

APIBackend = get_api_backend  # 别名
```

后端通过 `LLM_SETTINGS.backend` 字符串动态加载，默认使用 `LiteLLMAPIBackend`。

### 3.2 LiteLLM 后端实现（rdagent/oai/backend/litellm.py）

`LiteLLMAPIBackend` 是默认且推荐的后端，基于 [LiteLLM](https://github.com/BerriAI/litellm) 库实现，支持所有 LiteLLM 兼容的模型提供商。

**核心方法**：

1. **`_create_chat_completion_inner_function()`**：
   - 接收 `messages` 列表和可选的 `response_format`（Pydantic Model 用于结构化输出）
   - 调用 `litellm.completion()` 发起请求
   - 支持流式（stream）和非流式模式
   - 自动计算 token 数量和成本（`completion_cost()`）
   - 累计全局成本（`ACC_COST`）

2. **`_create_embedding_inner_function()`**：
   - 调用 `litellm.embedding()` 获取向量
   - 用于语义相似度计算（如假设去重）

3. **`get_complete_kwargs()`**：
   - 返回 model、temperature、max_tokens、reasoning_effort
   - 支持 `chat_model_map`：根据 logger tag 动态切换模型（如 Research Agent 用 o3，Developer Agent 用 GPT-4.1）

4. **`supports_response_schema()`**：
   - 检查模型是否支持结构化 JSON 输出
   - DeepSeek 等不支持时会自动降级

### 3.3 Prompt 构造与代码解析

**Prompt 模板系统**：RD-Agent 使用 YAML 文件 + Jinja2 风格的模板系统来构造 prompt：
- 模板文件位于各组件的 `prompts.yaml` 文件中
- 使用 `rdagent.utils.agent.tpl.T` 模板引擎渲染
- 包含系统提示、任务描述、历史代码、错误信息等上下文

**代码生成与验证流程**（以 FactorCoSTEER 为例）：

1. **CoSTEER 框架**（`rdagent/components/coder/CoSTEER/`）：是多 Agent 代码进化框架
   - `FactorCoSTEER` 继承 `CoSTEER`，组合了 `FactorEvaluatorForCoder`（评估器）和 `FactorMultiProcessEvolvingStrategy`（进化策略）
   - `develop(exp)` 方法接收实验对象，生成/修改代码

2. **代码解析**：
   - 生成的代码注入 `FBWorkspace.file_dict`
   - `all_codes` 属性提取所有 `.py` 文件内容（排除测试文件）
   - `get_codes(pattern)` 按正则筛选特定文件

3. **代码验证**：
   - 在 Docker 容器中执行（`env.run(entry, workspace_path)`）
   - 执行结果（stdout）被截断和过滤（`shrink_text` + `filter_redundant_text`）
   - 支持 pickle 缓存避免重复执行

### 3.4 反馈生成

反馈通过 `summarizer.generate_feedback()` 生成，类型为 `HypothesisFeedback`：
- `decision: bool`：假设是否被验证（是否改进）
- `observations`：实验观察
- `hypothesis_evaluation`：假设评估
- `new_hypothesis`：建议的新方向
- `code_change_summary`：代码变更摘要
- `acceptable`：整体是否可接受

异常情况下自动生成 `HypothesisFeedback(decision=False, reason=str(e))`。

### 3.5 迭代循环驱动

循环由 `LoopBase` 的异步引擎驱动：
- `asyncio.run(factor_loop.run(step_n, loop_n, all_duration))`
- 支持 `step_n`（单步数）、`loop_n`（循环数）、`all_duration`（总时长）控制
- `LoopMeta` 元类自动注册标记为步骤的方法，按依赖关系编排
- 并行控制：`get_unfinished_loop_cnt()` + `get_max_parallel()` 限制并发

---

## 四、Qlib 集成方式

### 4.1 架构定位

Qlib 是微软的开源量化投资平台，RD-Agent 与其深度集成：

```
rdagent/scenarios/qlib/          # Qlib 场景定义
├── experiment/                  # 实验模板和 workspace
│   ├── common.py               # 公共实验工具
│   ├── model/                  # 模型实验
│   └── factor/                 # 因子实验
├── components/                  # Qlib 专用组件
│   ├── coder/                  # Qlib 代码生成
│   ├── evaluator/              # Qlib 评估器
│   └── runner/                 # Qlib 运行器
└── proposal/                   # Qlib 假设生成
```

### 4.2 数据格式与特征系统

**基础特征集**：`rdagent.utils.qlib.ALPHA20`（Qlib 内置 Alpha20 因子集）

**因子定义格式**：
- 因子以 Python 文件形式存在（如 `feature_codes` 字典）
- 每个因子是一个可计算的表达式
- 支持 `base_factors.json`（JSON 字典：`feature_name -> expression`）

**时间分段配置**（通过环境变量）：
```bash
QLIB_FACTOR_TRAIN_START=2008-01-01
QLIB_FACTOR_TRAIN_END=2014-12-31
QLIB_FACTOR_VALID_START=2015-01-01
QLIB_FACTOR_VALID_END=2016-12-31
QLIB_FACTOR_TEST_START=2017-01-01
QLIB_FACTOR_TEST_END=2020-12-31
```

### 4.3 回测调用

回测通过 **Docker 环境**执行：
1. 代码注入 `FBWorkspace`（Python 文件 + YAML 配置）
2. `workspace.run(env, entry)` 在 Docker 中执行 Qlib 的工作流
3. Qlib 工作流 YAML 定义了数据加载 → 因子计算 → 模型训练 → 回测的完整流程
4. 执行结果通过 stdout 返回，包含 IC、IRR、Sharpe Ratio 等指标

**环境配置**：
- 默认使用 Docker（隔离执行）
- 可切换为 Conda（`MODEL_COSTEER_ENV_TYPE=conda`）

### 4.4 结果格式

- 实验结果存储在 `Experiment.running_info.result` 中
- 包含回测指标（IC、年化收益率、夏普比率等）
- 反馈由 Qlib 专用 Summarizer 解析 stdout 后生成

---

## 五、Web UI 架构

### 5.1 双模式 UI

RD-Agent 提供 **两种 UI 模式**：

#### 模式一：Streamlit UI（`rdagent ui`）
```bash
rdagent ui --port 19899 --log-dir <log_dir> [--debug]
```
- 基于 **Streamlit** 框架
- 读取本地日志文件（`.pkl` 格式）进行可视化
- 适合事后分析 R&D 过程
- 入口：`rdagent/log/ui/app.py`
- 配置（`rdagent/log/ui/conf.py`）：
  - `default_log_folders: ["./log"]`
  - `static_path: "./git_ignore_folder/static"`
  - `trace_folder: "./git_ignore_folder/traces"`
- 数据科学场景有独立 UI：`rdagent/log/ui/dsapp.py`

#### 模式二：Flask Server UI（`rdagent server_ui`）
```bash
rdagent server_ui --port 19899
```
- 基于 **Flask** + **CORS** 的实时服务器
- 前后端分离架构：
  - 后端：Flask API 服务器（`rdagent/log/server/app.py`）
  - 前端：独立构建的静态资源（`UI_SETTING.static_path`）
- 支持 **实时交互**：任务提交、日志流式查看、用户交互（人在回路）
- 默认端口：19899

### 5.2 Flask Server 核心功能

| API 端点 | 方法 | 功能 |
|----------|------|------|
| `/upload` | POST | 上传文件并启动新任务（选择场景、上传数据） |
| `/trace` | POST | 获取 trace 日志（增量返回，支持分页） |
| `/traces` | GET | 列出所有历史 trace |
| `/receive` | POST | 接收实时日志消息 |
| `/control` | POST | 控制任务（停止） |
| `/user_interaction/submit` | POST | 提交用户交互响应 |
| `/stdout` | GET | 下载任务的 stdout 日志文件 |
| `/favicon.ico` | GET | 静态资源 |

### 5.3 任务管理架构

`RDAgentTask` 是 Flask Server 的核心任务管理类：
- 每个任务在**独立进程**中运行（`multiprocessing.Process`）
- 通过两个 `multiprocessing.Queue` 实现**双向 IPC**：
  - `user_request_q`：Agent → 前端（请求用户输入）
  - `user_response_q`：前端 → Agent（返回用户决策）
- 任务状态管理：`start()` / `stop()` / `is_alive()` / `get_end_code()`

### 5.4 iframe 嵌入能力

- **Streamlit UI**：Streamlit 应用本身可以被 iframe 嵌入，但需要注意 `streamlit config` 中的 `server.headless` 和 CORS 设置
- **Flask Server UI**：作为标准 Flask 应用，启用了 `CORS(app)`，可以方便地通过 API 集成或 iframe 嵌入
- `.streamlit/config.toml` 存在，说明有 Streamlit 配置（仅 38 字节，基本配置）

---

## 六、配置系统

### 6.1 配置层级架构

RD-Agent 使用 **Pydantic Settings** 作为配置基础，所有配置类继承自 `ExtendedBaseSettings`：

```
ExtendedBaseSettings (rdagent/core/conf.py)
├── RD_AGENT_SETTINGS (全局设置)
├── LLMSettings (LLM 配置)
│   └── LiteLLMSettings (LiteLLM 特定配置, LITELLM_ 前缀)
├── BasePropSetting (循环配置)
│   ├── FACTOR_PROP_SETTING
│   ├── MODEL_PROP_SETTING
│   └── QUANT_PROP_SETTING
├── UIBasePropSetting (UI 配置, UI_ 前缀)
└── EnvConf (环境配置)
```

### 6.2 LLM 配置（对接 DeepSeek/OpenAI 兼容 API）

#### DeepSeek 配置（官方推荐配置）：
```bash
# .env 文件
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Embedding（DeepSeek 无 embedding 模型，使用 SiliconFlow）
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-m3
LITELLM_PROXY_API_KEY=sk-your-siliconflow-key
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
```

#### OpenAI 兼容 API 配置：
```bash
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_BASE=https://your-endpoint.com/v1
OPENAI_API_KEY=sk-your-key
```

#### Azure OpenAI 配置：
```bash
CHAT_MODEL=azure/<deployment-name>
EMBEDDING_MODEL=azure/<embedding-deployment>
AZURE_API_KEY=<key>
AZURE_API_BASE=<endpoint>
AZURE_API_VERSION=<version>
```

#### 关键配置参数说明：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `CHAT_MODEL` | LiteLLM 格式的模型名 | `gpt-4-turbo` |
| `EMBEDDING_MODEL` | Embedding 模型名 | `text-embedding-3-small` |
| `OPENAI_API_BASE` | Chat API 地址 | - |
| `OPENAI_API_KEY` | API Key | - |
| `REASONING_THINK_RM` | 移除 `<think>` 标签 | `False` |
| `CHAT_TEMPERATURE` | 温度 | `0.5` |
| `CHAT_STREAM` | 流式输出 | `True` |
| `MAX_PAST_MESSAGE_INCLUDE` | 包含的历史消息数 | `10` |
| `MAX_RETRY` | 重试次数 | `10` |
| `USE_CHAT_CACHE` | 启用 chat 缓存 | `False` |
| `CHAT_MODEL_MAP` | 按 tag 切换模型 | `{}` |

#### 模型切换（chat_model_map）：

支持为不同角色（如 Research Agent 和 Development Agent）配置不同模型：
```python
# 在 .env 中可以配置 CHAT_MODEL_MAP
# 格式: {"tag_pattern": {"model": "...", "temperature": 0.3}}
```

### 6.3 环境变量加载机制

- CLI 入口 `cli.py` 中首先执行 `load_dotenv(".env")`
- 所有 `ExtendedBaseSettings` 子类自动从环境变量读取
- 环境变量名自动映射（如 `chat_model` ↔ `CHAT_MODEL`）
- LiteLLM 配置使用 `LITELLM_` 前缀

### 6.4 Docker 配置

**Docker 环境管理**（`rdagent/utils/env.py`）：
- `DockerConf` 继承 `EnvConf`，包含 Docker 镜像、挂载路径等配置
- `Env.run()` 方法核心流程：
  1. 构建 entry 命令（添加 `timeout` 包裹）
  2. 检查缓存（基于代码内容 + 参数的 MD5 hash）
  3. 在 Docker 容器中执行（`docker` Python SDK）
  4. 支持 `retry_count`（默认 5 次）和 `retry_wait_seconds`（默认 10 秒）
  5. 超时控制（`running_timeout_period`，默认 3600 秒）
  6. 输出截断（`shrink_text` + `filter_redundant_text`）

**场景特定 Docker 配置**：
```bash
# 模型场景
MODEL_COSTEER_ENV_TYPE=docker  # 或 conda

# 数据科学场景
DS_CODER_COSTEER_ENV_TYPE=docker  # 或 conda
```

**Docker 要求**：
- 必须安装 Docker（`docker run hello-world` 可成功）
- 当前用户需有 Docker 命令的无 sudo 执行权限
- 仅支持 Linux 平台

---

## 七、CLI 使用方式

### 7.1 入口与安装

```bash
# 安装
pip install rdagent

# 或开发安装
git clone https://github.com/microsoft/RD-Agent
cd RD-Agent
make dev
```

CLI 入口定义在 `pyproject.toml`：
```toml
[project.scripts]
rdagent = "rdagent.app.cli:app"
```

使用 **Typer** 框架（基于 Click），提供子命令式 CLI。

### 7.2 完整命令列表

| 命令 | 说明 | 关键参数 |
|------|------|----------|
| `rdagent fin_factor` | 因子迭代循环 | `--path`（续跑）, `--step_n`, `--loop_n`, `--all_duration`, `--checkout/-c` |
| `rdagent fin_model` | 模型迭代循环 | 同上 |
| `rdagent fin_quant` | 因子+模型联合循环 | 同上 |
| `rdagent fin_factor_report` | 从财报提取因子 | `--report_folder`, `--path`, `--all_duration` |
| `rdagent general_model` | 论文模型复现 | `<URL or filepath>` |
| `rdagent data_science` | 数据科学/Kaggle | `--competition`, `--step_n`, `--loop_n`, `--timeout` |
| `rdagent llm_finetune` | LLM 微调 | `--benchmark`, `--dataset`, `--base_model`, `--loop_n` |
| `rdagent ui` | Streamlit UI | `--port`（默认 19899）, `--log-dir`, `--debug`, `--data_science` |
| `rdagent server_ui` | Flask Server UI | `--port`（默认 19899） |
| `rdagent ds_user_interact` | DS 实时交互 UI | `--port`（默认 19900） |
| `rdagent health_check` | 环境检查 | `--check-env/-e`, `--check-docker/-d`, `--check-ports/-p` |
| `rdagent collect_info` | 收集系统信息 | 无 |
| `rdagent grade_summary` | 评分摘要 | `<log_folder>` |

### 7.3 续跑（Session 恢复）

```bash
# 从已有 log 路径恢复
rdagent fin_factor --path <LOG_PATH>/__session__/1/0_propose --step_n 1

# checkout 控制
rdagent fin_factor --path <path> --no-checkout  # 不 checkout git
```

### 7.4 外部程序调用

RD-Agent 可以被外部程序通过以下方式调用：

**方式一：Python API 直接调用**
```python
from rdagent.app.qlib_rd_loop.factor import main as fin_factor
fin_factor(path=None, step_n=1, loop_n=5, checkout=True)
```

**方式二：Flask Server API 调用**
```python
# POST /upload 启动任务
import requests
resp = requests.post("http://localhost:19899/upload", data={
    "scenario": "Finance Data Building",
    "loops": "5",
}, files=[("files", open("data.csv", "rb"))])
trace_id = resp.json()["id"]

# POST /trace 轮询日志
logs = requests.post("http://localhost:19899/trace", json={
    "id": trace_id, "all": True
})
```

**方式三：子进程调用**
```bash
rdagent fin_factor --loop_n 5
```

---

## 八、组件间依赖与调用关系

### 8.1 核心调用链

```
CLI (cli.py)
  └── 场景入口 (app/qlib_rd_loop/factor.py)
       └── FactorRDLoop (继承 RDLoop)
            ├── hypothesis_gen.gen(trace) → Hypothesis
            │     └── 调用 LLM (APIBackend.build_messages_and_create_chat())
            ├── hypothesis2experiment.convert(hypothesis) → Experiment
            │     └── 调用 LLM 生成 sub_tasks
            ├── coder.develop(exp) → Experiment (带代码)
            │     └── FactorCoSTEER (CoSTEER 框架)
            │          ├── evolving_strategy → 调用 LLM 生成/修改代码
            │          ├── evaluator → 代码质量评估
            │          └── 迭代进化 (evolving_version=2)
            ├── runner.develop(exp) → Experiment (带结果)
            │     └── FBWorkspace.run(env, entry)
            │          └── DockerEnv.run() → Docker 容器执行
            └── summarizer.generate_feedback(exp, trace) → HypothesisFeedback
                  └── 调用 LLM 分析 stdout 结果
```

### 8.2 模块依赖图

```
app (应用层) ──依赖──→ components (组件层) ──依赖──→ core (核心层)
     │                      │                          │
     ├── qlib_rd_loop        ├── workflow/rd_loop        ├── experiment.py
     ├── data_science        ├── coder/CoSTEER           ├── proposal.py
     └── finetune            ├── evaluator/              ├── developer.py
                              └── runner/                 └── scenario.py
     │
     └── 依赖 → scenarios (场景层)
                  └── qlib/
                       ├── experiment/
                       ├── components/
                       └── proposal/

所有层 ──依赖──→ oai (LLM 层)
所有层 ──依赖──→ utils (工具层)
                  ├── env.py (Docker)
                  ├── workflow.py (循环引擎)
                  └── qlib.py
所有层 ──依赖──→ log (日志层)
```

### 8.3 CoSTEER 代码进化框架

CoSTEER（Code Synthesis and Testing Evolutionary Refinement）是 RD-Agent 的核心代码生成框架：

- **多 Agent 协作**：多个 Agent 并行生成/修改代码
- **评估驱动**：`CoSTEERMultiEvaluator` 评估代码质量
- **进化策略**：`FactorMultiProcessEvolvingStrategy` 控制进化方向
- **迭代优化**：默认 2 轮进化（`evolving_version=2`）
- **反馈传播**：进化轨迹的最终反馈通过 `prop_dev_feedback` 传递给下一组件

---

## 九、技术亮点与设计模式总结

### 9.1 关键设计模式

1. **工厂模式 + 动态导入**：所有组件通过字符串路径配置，`import_class()` 动态加载，实现了即插即用
2. **模板方法模式**：`LoopBase` + `LoopMeta` 元类定义循环骨架，子类重写具体步骤
3. **策略模式**：不同的 Evaluator/EvolvingStrategy/Coder 可互换
4. **DAG 追踪**：实验历史以有向无环图维护，支持分支探索和回溯
5. **检查点机制**：Workspace 支持 zip 级别的快照和恢复

### 9.2 工程亮点

- **LiteLLM 统一接口**：一个后端支持 100+ 模型提供商
- **Docker 隔离执行**：所有代码在容器中运行，安全且可复现
- **结果缓存**：基于代码内容 hash 的 pickle 缓存，避免重复执行
- **结构化输出**：支持 Pydantic Model 约束 LLM 输出格式
- **人在回路**：multiprocessing.Queue 实现 Agent 与用户的双向交互
- **成本追踪**：全局累计 API 调用成本

### 9.3 扩展性

- **自定义场景**：继承 `Scenario` + `RDLoop`，配置 `BasePropSetting`
- **自定义 Coder**：继承 `CoSTEER`，实现自己的 `EvolvingStrategy` 和 `Evaluator`
- **自定义 LLM 后端**：继承 `APIBackend`，实现 chat/embedding 方法
- **自定义环境**：继承 `Env`，实现 `prepare()` 和 `_run()` 方法

---

## 十、关键限制与注意事项

1. **仅支持 Linux**：Windows/macOS 不受支持（Docker 和符号链接依赖）
2. **Python 版本**：仅测试 3.10 和 3.11
3. **Docker 必需**：大多数场景需要 Docker（数据科学场景可选 Conda）
4. **API 成本**：每次迭代涉及多次 LLM 调用（假设生成 + 代码生成 + 评估 + 反馈），需注意成本
5. **Embedding 模型要求**：DeepSeek 等无 embedding 的模型需要额外配置 embedding 服务
6. **Reasoning 模型**：带 `<think>` 标签的模型需设置 `REASONING_THINK_RM=True`
7. **Web UI 新版**：`rdagent server_ui`（Flask）是新架构，目前不支持 `data_science` 场景

---

*本报告基于 RD-Agent 仓库 main 分支（2026-08-10）的源码分析编写。*
