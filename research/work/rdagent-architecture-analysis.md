# Microsoft RD-Agent 架构深度分析

> 分析时间: 2026-08-10
> 仓库: https://github.com/microsoft/RD-Agent
> 版本: main 分支最新

---

## 目录

1. [总体概述](#1-总体概述)
2. [目录结构](#2-目录结构)
3. [核心循环 (Hypothesis → Code → Execution → Feedback → Iteration)](#3-核心循环)
4. [Qlib 量化场景集成](#4-qlib-量化场景集成)
5. [配置系统](#5-配置系统)
6. [CLI 接口](#6-cli-接口)
7. [Web UI 架构](#7-web-ui-架构)
8. [Factor Proposal 机制](#8-factor-proposal-机制)
9. [DeepSeek 配置指南](#9-deepseek-配置指南)

---

## 1. 总体概述

RD-Agent 是微软开源的 **Research & Development Agent** 框架，旨在自动化工业界最关键的 R&D 流程。框架核心思想是将 R&D 过程拆解为两个关键组件：

- **R (Research/Hypothesis)**: 提出新想法/假设
- **D (Development/Implementation)**: 实现并验证这些想法

### 核心理念

```
Hypothesis → Code Generation → Execution → Feedback → New Hypothesis → ...
```

这是一个 **数据驱动的进化式框架 (Evolving Framework)**，通过 DAG (有向无环图) 结构追踪实验历史，支持假设的树状演化。

### 支持的场景

| 场景 | 路径 | 说明 |
|------|------|------|
| **Quant Factor** | `scenarios/qlib/` | 自动化量化因子研发 |
| **Quant Model** | `scenarios/qlib/` | 量化模型研发 |
| **Quant (Co-optimization)** | `scenarios/qlib/` | 因子-模型联合优化 |
| **Data Science** | `scenarios/data_science/ | Kaggle风格的数据科学竞赛 |
| **Kaggle** | `scenarios/kaggle/` | Kaggle 自动建模 |
| **LLM Fine-tuning** | `scenarios/finetune/` | LLM 微调优化 |
| **General Model** | `scenarios/general_model/` | 从论文提取模型结构 |
| **RL** | `scenarios/rl/` | 强化学习后训练流水线 |

---

## 2. 目录结构

```
rdagent/
├── rdagent/                          # 主包
│   ├── app/                          # 应用入口层 (CLI + 各场景的Loop)
│   │   ├── cli.py                    # 🔑 CLI 入口 (typer框架)
│   │   ├── qlib_rd_loop/             # Qlib R&D 循环应用
│   │   │   ├── factor.py             #   - 因子研发循环
│   │   │   ├── model.py              #   - 模型研发循环
│   │   │   ├── quant.py              #   - 因子+模型联合优化
│   │   │   ├── factor_from_report.py #   - 从研报提取因子
│   │   │   └── entry.py              #   - 入口包装
│   │   ├── data_science/             # 数据科学场景应用
│   │   ├── finetune/                 # LLM 微调场景
│   │   │   └── llm/                  #   LLM fine-tuning
│   │   ├── general_model/            # 通用模型提取
│   │   ├── kaggle/                   # Kaggle 场景
│   │   ├── benchmark/                # Agent² Benchmark
│   │   ├── rl/                       # 强化学习场景
│   │   ├── CI/                       # CI/CD 场景
│   │   └── utils/                    # 应用工具
│   │       ├── health_check.py       #   环境健康检查
│   │       └── info.py              #   系统信息收集
│   │
│   ├── core/                         # 🔑 核心框架 (抽象层)
│   │   ├── conf.py                   # 基础配置 (ExtendedBaseSettings)
│   │   ├── developer.py              # 开发者接口
│   │   ├── evaluation.py             # 评估框架 (EvaluableObj, Evaluator, Feedback)
│   │   ├── evolving_framework.py     # 🔑 进化框架核心 (Knowledge, Strategy, RAG)
│   │   ├── evolving_agent.py         # 进化Agent (串联整个循环)
│   │   ├── experiment.py             # 实验模型 (Experiment, ExpPlan, Task)
│   │   ├── proposal.py               # 🔑 假设与Trace系统 (Hypothesis, Trace DAG)
│   │   ├── scenario.py               # 场景抽象基类
│   │   ├── knowledge_base.py         # 知识库基类
│   │   ├── prompts.py                # 提示词基类
│   │   ├── interactor.py             # 交互器接口
│   │   ├── exception.py              # 异常定义
│   │   └── utils.py                  # 核心工具函数
│   │
│   ├── components/                   # 🔑 组件层 (可复用的功能模块)
│   │   ├── coder/                    # 代码生成器
│   │   │   ├── factor/               #   - 因子代码生成 (Qlib)
│   │   │   ├── model/                #   - 模型代码生成 (Qlib)
│   │   │   ├── data_science/         #   - 数据科学代码生成
│   │   │   └── ...
│   │   ├── proposal/                 # 假设提案器
│   │   │   ├── factor_exp_loader.py  #   - 因子实验加载器
│   │   │   └── ...
│   │   ├── runner/                   # 执行运行器
│   │   │   ├── qlib/                 #   - Qlib 回测运行
│   │   │   └── ...
│   │   ├── evaluator/                # 评估器
│   │   ├── knowledge_management/     # 知识管理
│   │   ├── workflow/                 # 工作流
│   │   ├── loader/                   # 加载器
│   │   ├── document_reader/          # 文档阅读器
│   │   ├── interactor/               # 交互组件
│   │   ├── agent/                    # Agent组件
│   │   └── benchmark/                # 基准测试
│   │
│   ├── scenarios/                    # 🔑 场景层 (具体领域实现)
│   │   ├── qlib/                     # Qlib 量化场景 ⭐
│   │   │   ├── factor/               #   因子研发
│   │   │   │   ├── proposer.py       #     因子提案器
│   │   │   │   ├── exp.py            #     因子实验定义
│   │   │   │   └── ...
│   │   │   ├── model/                #   模型研发
│   │   │   ├── quant/                #   联合优化
│   │   │   └── ...
│   │   ├── data_science/             # 数据科学场景
│   │   ├── kaggle/                   # Kaggle 场景
│   │   ├── finetune/                 # 微调场景
│   │   ├── general_model/            # 通用模型场景
│   │   ├── rl/                       # 强化学习场景
│   │   └── shared/                   # 共享场景组件
│   │
│   ├── oai/                          # 🔑 LLM 后端层
│   │   ├── llm_conf.py               # 🔑 LLM 配置 (LLMSettings)
│   │   ├── llm_utils.py              # LLM 工具函数
│   │   ├── backend/                  # LLM API 后端实现
│   │   │   ├── LiteLLMAPIBackend     #   默认 (LiteLLM)
│   │   │   └── ...
│   │   └── utils/                    # LLM 工具
│   │
│   ├── log/                          # 日志与可视化层
│   │   ├── ui/                       # Streamlit UI
│   │   │   ├── app.py                #   主 UI 应用
│   │   │   ├── dsapp.py              #   数据科学 UI
│   │   │   └── ds_user_interact.py   #   数据科学交互 UI
│   │   ├── server/                   # Flask 日志服务器
│   │   └── mle_summary.py            # MLE-bench 总结
│   │
│   └── utils/                        # 通用工具
│       ├── workflow.py               # 工作流工具
│       └── ...
│
├── pyproject.toml                    # 项目配置
├── .env.example                      # 环境变量模板
├── Makefile                          # 构建/开发命令
├── requirements.txt                  # 依赖
└── docs/                             # 文档
```

---

## 3. 核心循环

### 3.1 架构层级

RD-Agent 的核心循环基于 **进化式框架 (Evolving Framework)**，由以下抽象层组成：

```
┌─────────────────────────────────────────────────────────────┐
│                    EvolvingAgent (core/evolving_agent.py)    │
│                   ┌─────────────────────────────┐           │
│                   │  1. RAGStrategy.query()     │           │
│                   │  2. ExpPlanner.plan()       │           │
│                   │  3. ExpGen.generate()       │           │
│                   │  4. Coder.develop()         │           │
│                   │  5. Runner.run()            │           │
│                   │  6. Evaluator.evaluate()    │           │
│                   │  7. RAGStrategy.generate()  │           │
│                   └─────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 核心类详解

#### `rdagent/core/proposal.py` - 假设与追踪系统

**`Hypothesis` 类**:
```python
class Hypothesis:
    """假设 - 一个可测试的研究想法"""
    def __init__(self,
        hypothesis: str,          # 假设内容
        reason: str,              # 假设原因
        conclusion_reason: str,   # 结论推理
        conclusion_observation: str,  # 观察结论
        conclusion_justification: str,  # 结论论证
        conclusion_knowledge: str,  # 结论知识
    )
```

**`ExperimentFeedback` 类**: 实验执行后的反馈
```python
class ExperimentFeedback(Feedback):
    def __init__(self,
        reason: str,
        decision: bool,           # 是否成功/有提升
        code_change_summary: str | None = None,
        eda_improvement: str | None = None,
        exception: Exception | None = None,
    )
```

**`HypothesisFeedback` 类**: 假设反馈，包含观察和评估
```python
class HypothesisFeedback(ExperimentFeedback):
    def __init__(self,
        ...,
        observations: str | None = None,        # 观察结果
        hypothesis_evaluation: str | None = None,  # 假设评估
        new_hypothesis: str | None = None,       # 新假设方向
        acceptable: bool | None = None,          # 是否可接受
    )
```

**`Trace` 类**: 实验追踪的 DAG 结构
```python
class Trace:
    NodeType = tuple[Experiment, ExperimentFeedback]  # 节点 = (实验, 反馈)
    NEW_ROOT: tuple = ()
    SEL_LATEST_SOTA: tuple = (-1,)

    def __init__(self, scen, knowledge_base=None):
        self.hist: list[NodeType] = []       # 历史实验列表
        self.dag_parent: list[tuple[int, ...]] = []  # DAG父节点
        self.idx2loop_id: dict[int, int] = {}  # ID映射
        self.current_selection: tuple[int, ...] = self.SEL_LATEST_SOTA

    def get_sota_hypothesis_and_experiment(self) -> tuple[Hypothesis|None, Experiment|None]:
        """获取当前 SOTA (State of the Art) 假设和实验"""
        ...
```

**选择器类**:
- `CheckpointSelector`: 抽象基类，决定从哪个检查点继续
- `SOTAExpSelector`: 选择 SOTA 实验继续演化

**规划器与生成器**:
- `ExpPlanner(ABC)`: 抽象规划器，`plan(trace) -> ASpecificPlan`
- `ExpGen(ABC)`: 实验生成器，根据场景和Trace生成新实验

#### `rdagent/core/evolving_framework.py` - 进化框架

**核心抽象类**:

```python
class EvolvableSubjects(EvaluableObj):
    """被进化的目标对象"""
    def clone(self) -> 'EvolvableSubjects':
        return copy.deepcopy(self)

@dataclass
class EvStep(Generic[ASpecificEvolvableSubjects]):
    """进化的一个步骤"""
    evolvable_subjects: ASpecificEvolvableSubjects
    queried_knowledge: QueriedKnowledge | None = None
    feedback: Feedback | None = None

class EvolvingStrategy(ABC):
    """进化策略 - 核心抽象"""
    def __init__(self, scen: Scenario): ...

    @abstractmethod
    def evolve_iter(self,
        evo: ASpecificEvolvableSubjects,
        queried_knowledge: QueriedKnowledge | None = None,
        evolving_trace: list[EvStep] | None = None,
    ) -> Generator[ASpecificEvolvableSubjects, None, None]:
        """迭代进化生成器 - yield 部分结果"""

class RAGStrategy(ABC):
    """检索增强生成策略"""
    @abstractmethod
    def query(self, ...) -> QueriedKnowledge | None:
        """查询相关知识"""

    @abstractmethod
    def generate_knowledge(self,
        evolving_trace: list[EvStep],
        return_knowledge: bool = False,
    ) -> Knowledge | None:
        """从实验历史中生成新知识"""

class IterEvaluator(Evaluator):
    """迭代评估器 - 支持逐步评估"""
    def evaluate(self, eo: EvaluableObj) -> Feedback:
        """默认实现: 运行 evaluate_iter 到完成"""

    @abstractmethod
    def evaluate_iter(self) -> Generator[Feedback, EvaluableObj | None, Feedback]:
        """迭代评估 - yield 每个阶段的反馈"""
```

#### `rdagent/core/experiment.py` - 实验模型

```python
class Experiment(FrozenMutable):
    """实验定义"""
    # 包含实验配置、代码、输入输出等

class ExperimentPlan:
    """实验计划"""
    # 定义实验的各阶段

class Task:
    """单个任务"""
    # 实验中的具体任务
```

### 3.3 循环执行流程

```
Loop 开始
   │
   ├── 1. RAGStrategy.query(evo, trace)
   │      └── 从知识库查询相关历史知识
   │
   ├── 2. ExpPlanner.plan(trace)
   │      └── 基于Trace DAG规划下一步实验
   │
   ├── 3. ExpGen.generate(scen, trace, plan)
   │      └── 生成新假设(Hypothesis)和实验定义
   │
   ├── 4. Coder.develop(exp)
   │      └── LLM生成代码 (因子代码/模型代码)
   │
   ├── 5. Runner.run(exp)
   │      └── 通过Docker/Conda执行代码
   │
   ├── 6. Evaluator.evaluate(exp)
   │      └── 评估结果，生成Feedback
   │
   ├── 7. RAGStrategy.generate_knowledge(trace)
   │      └── 从反馈中提取知识更新知识库
   │
   └── → 回到步骤1，基于新Trace继续
```

---

## 4. Qlib 量化场景集成

### 4.1 目录结构

```
rdagent/scenarios/qlib/
├── developer/                       # 开发执行层
│   ├── factor_coder.py              #   因子Coder入口 (薄包装)
│   ├── factor_runner.py             #   🔑 QlibFactorRunner (9.8KB)
│   ├── feedback.py                  #   🔑 QlibFactorExperiment2Feedback, QlibModelExperiment2Feedback
│   ├── model_coder.py               #   模型Coder入口
│   ├── model_runner.py              #   QlibModelRunner
│   └── utils.py                     #   process_factor_data 等工具
├── docker/                          # Docker执行环境配置
├── experiment/                      # 实验定义层
│   ├── factor_data_template/        #   因子数据模板
│   ├── factor_experiment.py         #   🔑 QlibFactorExperiment, QlibFactorScenario
│   ├── factor_from_report_experiment.py
│   ├── factor_template/             #   Qlib YAML配置 + 代码模板
│   ├── model_experiment.py          #   模型实验定义
│   ├── model_template/              #   模型模板
│   ├── prompts.yaml                 #   场景提示词 (16KB)
│   ├── quant_experiment.py          #   🔑 QlibQuantScenario (联合优化)
│   ├── utils.py                     #   get_data_folder_intro
│   └── workspace.py                 #   QlibFBWorkspace
├── factor_experiment_loader/        # 因子实验加载器
├── proposal/                        # 🔑 假设提案层
│   ├── bandit.py                    #   Bandit动作选择器 (多臂老虎机)
│   ├── factor_proposal.py           #   🔑 QlibFactorHypothesisGen, QlibFactorHypothesis2Experiment
│   ├── model_proposal.py            #   模型假设生成
│   └── quant_proposal.py            #   联合优化假设生成
└── prompts.yaml                     # Qlib顶层提示词 (18.7KB)
```

### 4.1.1 应用入口层 (`rdagent/app/qlib_rd_loop/`)

```
rdagent/app/qlib_rd_loop/
├── conf.py                          # 🔑 配置: FactorBasePropSetting, ModelBasePropSetting, QuantBasePropSetting
├── factor.py                        # 🔑 FactorRDLoop 入口 (因子研发循环)
├── factor_from_report.py            # 从研报提取因子
├── model.py                         # ModelRDLoop 入口
├── prompts.yaml                     # 应用层提示词
└── quant.py                         # QuantRDLoop 入口 (联合优化)
```

### 4.2 因子实验流程 (详细)

#### 步骤1: 因子假设生成 (`QlibFactorHypothesisGen`)

位于 `rdagent/scenarios/qlib/proposal/factor_proposal.py`

```python
class QlibFactorHypothesisGen(FactorHypothesesGen):
    def prepare_context(self, trace: Trace):
        # 构建LLM上下文:
        # - hypothesis_and_feedback: 历史假设和反馈
        # - last_hypothesis_and_feedback: 最近一轮
        # - RAG: 自适应引导
        #   - <15轮: "先尝试最简单/最快的因子"
        #   - ≥15轮: "尝试能获得高IC的因子(基于ML)"
        # - hypothesis_output_format: 输出格式
        # - hypothesis_specification: 因子规范
    
    def convert_response(self, response: str) -> QlibFactorHypothesis:
        # 解析JSON响应，包含字段:
        # hypothesis, reason, concise_reason,
        # concise_observation, concise_justification, concise_knowledge
```

#### 步骤2: 假设转实验 (`QlibFactorHypothesis2Experiment`)

```python
class QlibFactorHypothesis2Experiment(FactorHypotheses2Experiment):
    def prepare_context(self, hypothesis, trace):
        # 使用 QlibQuantScenario.get_scenario_all_desc(action="factor")
        # 注入 factor_experiment_output_format
        # 过滤历史中 "factor" action 的假设和反馈
    
    def convert_response(self, response, hypothesis, trace) -> FactorExperiment:
        # 解析JSON: {因子名: {description, formulation, variables}}
        # 为每个因子创建 FactorTask(factor_name, factor_description, factor_formulation, variables)
        # 返回 QlibFactorExperiment(tasks, hypothesis=hypothesis)
```

#### 步骤3: 因子代码生成 (CoSTEER系统)

位于 `rdagent/components/coder/factor_coder/factor.py`

```python
class FactorTask(CoSTEERTask):
    def __init__(self, factor_name, factor_description, factor_formulation,
                 variables: dict = {}, resource: str = None,
                 factor_implementation: bool = False, ...):
        self.factor_name = factor_name
        # ... 因子代码生成任务定义

class FactorFBWorkspace(FBWorkspace):
    # 因子反馈工作区 - 管理因子代码的执行环境
    pass
```

CoSTEER (`components/coder/CoSTEER/`) 是一个**自进化代码生成系统**，包含:
- 代码生成、评估、反馈的迭代循环
- 支持多语言代码生成
- 集成单元测试和功能测试

#### 步骤4: 因子回测执行 (`QlibFactorRunner`)

位于 `rdagent/scenarios/qlib/developer/factor_runner.py` (9.8KB)

通过 Docker 执行 Qlib 回测脚本。

#### 步骤5: 反馈生成 (`QlibFactorExperiment2Feedback`)

位于 `rdagent/scenarios/qlib/developer/feedback.py` (8KB)

将回测结果转换为结构化反馈，包含性能指标和改进建议。

### 4.3 数据格式

- **因子定义**: `FactorTask` 包含 `factor_name`, `factor_description`, `factor_formulation`, `variables`
- **因子代码**: Python代码，使用Qlib数据API (`D.features`) 获取行情数据并计算
- **回测配置**: Qlib YAML配置文件 (`factor_template/` 目录下)
- **回测结果**: 包含 IC (Information Coefficient)、ICIR、Rank IC、年化收益、夏普比率等
- **反馈格式**: `HypothesisFeedback` 包含 `observations`, `hypothesis_evaluation`, `new_hypothesis`, `acceptable`, `eda_improvement`

### 4.4 回测调用与执行环境

通过 Docker 执行 Qlib 回测脚本。配置通过 `rdagent/app/qlib_rd_loop/conf.py`:

```python
class FactorBasePropSetting(BasePropSetting):
    model_config = SettingsConfigDict(env_prefix="QLIB_FACTOR_")
    
    # 组件类路径 (字符串引用，支持替换)
    scen: str = "rdagent.scenarios.qlib.experiment.factor_experiment.QlibFactorScenario"
    hypotheses_gen: str = "rdagent.scenarios.qlib.proposal.factor_proposal.QlibFactorHypothesisGen"
    hypotheses2experiment: str = "rdagent.scenarios.qlib.proposal.factor_proposal.QlibFactorHypothesis2Experiment"
    coder: str = "rdagent.scenarios.qlib.developer.factor_coder.QlibFactorCoSTEER"
    runner: str = "rdagent.scenarios.qlib.developer.factor_runner.QlibFactorRunner"
    summarizer: str = "rdagent.scenarios.qlib.developer.feedback.QlibFactorExperiment2Feedback"
    
    evolving_n: int = 10  # 每轮进化次数
```

环境可以是:
- `MODEL_CODER_ENV_TYPE=docker` (推荐，隔离执行)
- `MODEL_CODER_ENV_TYPE=conda` (本地Conda环境)

### 4.5 时间段配置

通过环境变量配置:
```bash
QLIB_FACTOR_TRAIN_START=2008-01-01
QLIB_FACTOR_TRAIN_END=2014-12-31
QLIB_FACTOR_VALID_START=2015-01-01
QLIB_FACTOR_VALID_END=2016-12-31
QLIB_FACTOR_TEST_START=2017-01-01
QLIB_FACTOR_TEST_END=2020-12-31
```

---

## 5. 配置系统

### 5.1 配置层次

```
rdagent/core/conf.py    → ExtendedBaseSettings (Pydantic基础设置)
rdagent/oai/llm_conf.py → LLMSettings (LLM配置)
.env 文件               → 环境变量 (被 dotenv 加载)
```

### 5.2 `llm_conf.py` 详解

`rdagent/oai/llm_conf.py` 是 LLM 配置的核心文件:

```python
class LLMSettings(ExtendedBaseSettings):
    # === 后端配置 ===
    backend: str = "rdagent.oai.backend.LiteLLMAPIBackend"

    # === 模型配置 ===
    chat_model: str = "gpt-4-turbo"
    embedding_model: str = "text-embedding-3-small"

    # === 推理控制 ===
    reasoning_effort: Literal["low", "medium", "high"] | None = None
    enable_response_schema: bool = True
    reasoning_think_rm: bool = False  # 移除 <think>...</think> 标签

    # === 日志 ===
    log_llm_chat_content: bool = True

    # === Azure 配置 (已弃用) ===
    use_azure: bool = False  (deprecated)
    chat_use_azure: bool = False
    embedding_use_azure: bool = False

    # === 重试与缓存 ===
    max_retry: int = 10
    retry_wait_seconds: int = 1
    dump_chat_cache: bool = False
    use_chat_cache: bool = False
    use_embedding_cache: bool = False
    prompt_cache_path: str = str(Path.cwd() / "prompt_cache.db")
    max_past_message_include: int = 10
    timeout_fail_limit: int = 10
    violation_fail_limit: int = 1

    # === Chat 模型 API 配置 ===
    openai_api_key: str = ""
    openai_api_base: str = ""
    chat_openai_api_key: str | None = None
    chat_openai_base_url: str | None = None

    # === Chat 参数 ===
    chat_temperature: float = 0.5
    chat_stream: bool = True
    chat_seed: int | None = None
    chat_frequency_penalty: float = 0.0
    chat_presence_penalty: float = 0.0
    chat_token_limit: int = 100000
    default_system_prompt: str = "You are an AI assistant..."
    system_prompt_role: str = "system"

    # === Embedding 配置 ===
    embedding_openai_api_key: str = ""
    embedding_openai_base_url: str = ""
    embedding_max_str_num: int = 50
    embedding_max_length: int = 8192

    # === 离线 Llama 2 配置 ===
    use_llama2: bool = False
    llama2_ckpt_dir: str = "Llama-2-7b-chat"
    ...

    # === GCR (服务器) 端点配置 ===
    use_gcr_endpoint: bool = False
    gcr_endpoint_type: str = "llama2_70b"  # or "llama3_70b", "phi2", "phi3_4k", "phi3_128k"
    ...

    # === DeepSeek 配置 ===
    chat_use_azure_deepseek: bool = False
    chat_azure_deepseek_endpoint: str = ""
    chat_azure_deepseek_key: str = ""

    # === 模型映射 ===
    chat_model_map: dict[str, dict[str, str]] = {}

LLM_SETTINGS = LLMSettings()  # 全局单例
```

### 5.3 配置优先级

1. 环境变量 (`.env` 文件或 shell 环境)
2. `LLMSettings` 的默认值
3. Pydantic 的 `ExtendedBaseSettings` 自动从环境变量读取

---

## 6. CLI 接口

### 6.1 入口

```python
# pyproject.toml
[project.scripts]
rdagent = "rdagent.app.cli:app"
```

CLI 使用 **Typer** 框架，入口为 `rdagent/app/cli.py`。启动时自动加载 `.env` 文件。

### 6.2 可用命令

| 命令 | 说明 | 关键参数 |
|------|------|---------|
| `rdagent fin_factor` | 量化因子研发循环 | `--step_n`, `--loop_n`, `--all_duration`, `-C/--checkout` |
| `rdagent fin_model` | 量化模型研发循环 | 同上 |
| `rdagent fin_quant` | 因子+模型联合优化 | 同上 |
| `rdagent fin_factor_report` | 从研报提取因子 | `--report_folder`, `--path`, `-C` |
| `rdagent general_model` | 从论文提取模型结构 | `--report_file_path` |
| `rdagent data_science` | 数据科学 Agent | `--path`, `--step_n`, `--loop_n`, `--timeout`, `--competition` |
| `rdagent llm_finetune` | LLM 微调循环 | `--benchmark`, `--dataset`, `--base_model`, `--step_n`, `--loop_n` |
| `rdagent ui` | 启动 Web UI | `--port` (默认19899), `--log_dir`, `--debug`, `--data_science` |
| `rdagent server_ui` | 启动 Flask 日志服务器 | `--port` |
| `rdagent health_check` | 环境健康检查 | `--check_env`, `--check_docker`, `--check_ports` |
| `rdagent collect_info` | 收集系统信息 | 无 |
| `rdagent grade_summary` | 成绩总结 | `--log_folder` |
| `rdagent ds_user_interact` | 数据科学用户交互 | `--port` (默认19900) |

### 6.3 Headless 运行

**可以完全 headless 运行。** 只需调用对应的循环命令:

```bash
# 因子研发 - 运行10步
rdagent fin_factor --step_n 10

# 因子研发 - 运行5个完整循环
rdagent fin_factor --loop_n 5

# 数据科学 - 不使用Docker checkout
rdagent fin_factor --no-checkout

# 后台运行
rdagent fin_factor --loop_n 10 --no-checkout > output.log 2>&1 &
```

UI 是可选的，通过 `rdagent ui` 启动 Streamlit 可视化界面查看日志。

---

## 7. Web UI 架构

### 7.1 技术栈

- **前端**: **Streamlit** (Python Web框架)
- **日志服务器**: **Flask** (`rdagent/log/server/`)
- **不是前后端分离架构** — Streamlit 应用既是前端也是后端
- **实时追踪**: Flask 服务器提供实时日志和 trace 查看

### 7.2 UI 组件

```
rdagent/log/ui/
├── app.py                    # 主 Streamlit 应用 (通用)
├── dsapp.py                  # 数据科学专用 Streamlit 应用
├── ds_user_interact.py       # 数据科学用户交互界面
```

### 7.3 启动方式

```bash
# 启动 Streamlit UI (默认端口19899)
rdagent ui --port 19899

# 启动Flask日志服务器 (实时trace查看)
rdagent server_ui --port 19899

# 数据科学场景UI
rdagent ui --data_science
```

### 7.4 可嵌入性

- Streamlit 本质上是独立运行的 Web 应用，**不适合直接嵌入其他Web应用**
- Flask 日志服务器 (`rdagent/log/server/`) 可以作为 API 后端被其他应用调用
- 可以通过 Docker 部署整个系统
- 前端展示在 `.streamlit/config.toml` 中有基本配置

```toml
# .streamlit/config.toml
[server]
port = 19899
```

### 7.5 新版 Web UI (2025更新)

README 中提到:
> We release a new frontend that can be built and served by `rdagent server_ui` for real-time interaction and trace viewing, currently excluding the `data_science` scenario.

`server_ui` 命令启动的是一个 Flask 服务，提供更现代的前端体验。

---

## 8. Factor Proposal 机制

### 8.1 因子提案器架构

因子提案在 `rdagent/scenarios/qlib/proposal/factor_proposal.py` 中实现。

#### 核心类: `QlibFactorHypothesisGen(FactorHypothesesGen)`

```
输入: Trace (历史实验DAG) + Scenario (Qlib场景)
  │
  ├── 1. prepare_context(trace) — 构建LLM上下文
  │      ├── hypothesis_and_feedback (历史，来自 prompts.yaml 模板)
  │      ├── last_hypothesis_and_feedback (最近一轮)
  │      ├── RAG (自适应引导策略):
  │      │      < 15轮: "先尝试最简单/最快的因子"
  │      │      ≥ 15轮: "尝试能获得高IC的因子(基于ML)"
  │      ├── hypothesis_output_format (输出格式)
  │      └── hypothesis_specification (因子规范)
  │
  ├── 2. LLM 生成 (调用 create_chat_completion)
  │
  └── 3. convert_response(response) → QlibFactorHypothesis
         解析JSON，包含: hypothesis, reason, concise_reason,
         concise_observation, concise_justification, concise_knowledge
```

#### 核心类: `QlibFactorHypothesis2Experiment(FactorHypotheses2Experiment)`

将假设转化为具体的因子实验:

```python
# 输入: hypothesis (假设) + trace (历史)
# 输出: QlibFactorExperiment

# prepare_context 注入:
# - QlibQuantScenario.get_scenario_all_desc(action="factor")
# - factor_experiment_output_format (来自 prompts.yaml)
# - 历史中 "factor" action 的假设和反馈

# convert_response 解析JSON:
# {"factor_name_1": {"description": "...", "formulation": "...", "variables": {...}},
#  "factor_name_2": {...}}

# 创建 FactorTask 列表
```

### 8.2 Prompt 系统架构

RD-Agent 使用 **YAML 文件管理提示词**，而非硬编码:

- `rdagent/scenarios/qlib/prompts.yaml` (18.7KB) — Qlib场景顶层提示词
- `rdagent/scenarios/qlib/experiment/prompts.yaml` (16KB) — 实验相关提示词
- `rdagent/components/coder/factor_coder/prompts.yaml` (12.5KB) — 因子代码生成提示词
- `rdagent/app/qlib_rd_loop/prompts.yaml` — 应用层提示词

提示词通过 `T()` 函数加载 (类似 i18n 的模板系统):
```python
from rdagent.core.prompts import T

prompt = T("scenarios.qlib.prompts:hypothesis_and_feedback").render(
    trace=trace,
    scen=scen
)
```

关键 prompt 模板包括:
- `hypothesis_and_feedback` — 历史假设和反馈渲染
- `last_hypothesis_and_feedback` — 最近一轮渲染
- `factor_experiment_output_format` — 因子实验输出格式
- `hypothesis_output_format` — 假设输出格式
- `hypothesis_specification` — 因子假设规范

### 8.3 假设输出格式

LLM 返回的假设 JSON 格式:

```json
{
  "hypothesis": "新因子的假设描述",
  "reason": "为什么这个因子可能有效",
  "concise_reason": "简洁原因",
  "concise_observation": "简洁观察",
  "concise_justification": "简洁论证",
  "concise_knowledge": "可提取的知识"
}
```

### 8.4 Trace DAG 演化

```
假设1 (成功, IC=0.05)
  ├── 假设1a (变体A, 失败)
  ├── 假设1b (变体B, 成功, IC=0.07) ← SOTA
  │     ├── 假设1b-i (改进, IC=0.08) ← 新SOTA
  │     └── 假设1b-ii (不同方向, 失败)
  └── 假设1c (变体C, 成功, IC=0.06)
```

Trace 的 DAG 结构允许:
- 从 SOTA 节点继续演化 (默认)
- 从任意检查点分支
- 追踪假设的演化谱系

---

## 9. DeepSeek 配置指南

### 9.1 通过 LiteLLM 后端配置 (推荐)

RD-Agent 默认使用 **LiteLLM** 作为 LLM API 后端，支持 DeepSeek:

**方式一: 直接使用 DeepSeek API**

在项目根目录创建 `.env` 文件:
```bash
# .env
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# Embedding (DeepSeek暂不提供embedding，需用其他服务)
EMBEDDING_MODEL=liteLLM_proxy/BAII/bge-m3
LITELLM_PROXY_API_KEY=your-siliconflow-api-key
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
```

**方式二: 通过 OpenAI-compatible API**

```bash
# .env
CHAT_MODEL=openai/deepseek-chat  # LiteLLM的OpenAI provider前缀
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_API_BASE=https://api.deepseek.com/v1

# 或者使用 chat_ 前缀的独立配置
CHAT_MODEL=deepseek-chat
CHAT_OPENAI_API_KEY=sk-your-deepseek-api-key
CHAT_OPENAI_BASE_URL=https://api.deepseek.com/v1
```

**方式三: 使用 DeepSeek 官方API (LiteLLM 内置支持)**

```bash
# .env
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
```

### 9.2 高级配置

```bash
# 推理强度 (如果模型支持)
REASONING_EFFORT=medium

# 温度
CHAT_TEMPERATURE=0.5

# Token限制
CHAT_TOKEN_LIMIT=64000

# 禁用结构化响应 (某些模型不支持)
ENABLE_RESPONSE_SCHEMA=false

# 启用推理标签移除 (DeepSeek-R1等模型的<think>标签)
REASONING_THINK_RM=true
```

### 9.3 完整可用的 DeepSeek .env 模板

```bash
# ===== DeepSeek 配置 =====
# Chat模型
CHAT_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=sk-your-key-here

# Embedding模型 (使用SiliconFlow)
EMBEDDING_MODEL=liteLLM_proxy/BAII/bge-m3
LITELLM_PROXY_API_KEY=your-siliconflow-key
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1

# ===== 执行环境 =====
# Qlib因子场景使用Docker
MODEL_CODER_ENV_TYPE=docker

# ===== 因子时间段 =====
QLIB_FACTOR_TRAIN_START=2008-01-01
QLIB_FACTOR_TRAIN_END=2014-12-31
QLIB_FACTOR_VALID_START=2015-01-01
QLIB_FACTOR_VALID_END=2016-12-31
QLIB_FACTOR_TEST_START=2017-01-01
QLIB_FACTOR_TEST_END=2020-12-31
```

---

## 10. 关键架构特点总结

### 10.1 设计模式

| 模式 | 实现位置 | 说明 |
|------|---------|------|
| **进化式框架** | `core/evolving_framework.py` | 基于生成器的迭代进化 |
| **DAG追踪** | `core/proposal.py:Trace` | 假设的树状/图状演化 |
| **策略模式** | `EvolvingStrategy`, `RAGStrategy` | 可插拔的进化策略 |
| **模板方法** | `IterEvaluator` | 标准流程+可覆盖步骤 |
| **依赖注入** | `Scenario` 注入到各组件 | 场景驱动的配置 |
| **Pydantic配置** | `core/conf.py`, `oai/llm_conf.py` | 类型安全的配置管理 |

### 10.2 LLM集成

- **默认后端**: LiteLLM (`rdagent.oai.backend.LiteLLMAPIBackend`)
- **支持的Provider**: OpenAI, Azure OpenAI, DeepSeek, Llama2/3 (离线), SiliconFlow, Phi, GCR端点
- **特性**: 流式输出, 重试机制, 缓存, Schema约束输出, Temperature控制
- **Embedding**: 支持独立配置embedding模型

### 10.3 代码执行

- **Docker** (推荐): 隔离的代码执行环境
- **Conda**: 本地Conda环境
- 通过 `*_CODER_ENV_TYPE` 环境变量控制

### 10.4 扩展性

- 新增场景: 继承 `Scenario` + 实现 `EvolvingStrategy` + `ExpGen` + `Evaluator`
- 新增Coder: 继承 `Coder` 基类
- 新增Runner: 继承 `Runner` 基类
- 新增LLM后端: 继承 APIBackend

---

> **注**: 本分析基于 RD-Agent main 分支的代码。具体实现细节可能随版本更新而变化。建议参考 [官方文档](https://rdagent.readthedocs.io) 获取最新信息。
