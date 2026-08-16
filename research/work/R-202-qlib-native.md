# R-202 Qlib 原生开箱即用能力 & 因子挖掘替代项目

> 数据来源：Microsoft Qlib README、qlib.readthedocs.io（workflow / data / initialization 页面）、examples/benchmarks。
> 调研时间：2026-08-12

## 1. 核心结论：Qlib 不依赖 RD-Agent 也能完整跑因子 + 回测

Qlib 是**独立的 AI 量化平台**（pyqlib，pip 安装），自身就带完整的"数据 → 特征 → 模型 → 回测"闭环。RD-Agent 只是其上层"自动化 R&D"的可选增强，**不是运行因子流水线的前提**。RD-Agent 官方定位为"LLM-Based Autonomous Evolving Agents for Industrial Data-Driven R&D"（arXiv 2505.15155，Qlib 配套），用于自动因子挖掘 + 模型优化；没有它，Qlib 的手动 workflow 依然完整可用。

## 2. 开箱即用的官方能力（无需安装 RD-Agent）

### 2.1 数据层（Data Layer）
- 官方提供即用数据集（.bin 格式），支持 A 股（cn）与美股（us）：
  ```
  python scripts/get_data.py qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn
  ```
- 提供表达式引擎（expression engine，如 `Ref($close,60)/$close`）、Data Handler 内置 processor（标准化等）、Dataset 构造、缓存与实验管理（Recorder）。
- 初始化：
  ```python
  import qlib
  from qlib.constant import REG_CN
  qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)
  ```

### 2.2 开箱即用特征集（内置 Alpha158 / Alpha360）
Qlib `qlib/contrib/data/handler.py` 提供两套官方特征集，A 股/美股都可用：
- **Alpha158**：158 个量价类技术因子（K 线/振幅/量比/动量/波动等），分 K线、价格、量、波动率等子组；官方基准常用"selected 20 features"子集。
- **Alpha360**：360 个特征（常为过去 20 日 × 18 类滚动量价特征的高维表示），适合深度模型。
- 均可直接作为 `DatasetH` 的 handler，无需自己造因子。

### 2.3 开箱即用模型（examples/benchmarks）
官方内置大量可直接训练的模型，含经典与深度模型：
- GBDT 类：**LightGBM（LGBModel）**、XGBoost（xgboost）、CatBoost（catboost）等
- 线性/MLP：**Linear**、MLP（mlp）、DoubleEnsemble 等
- 深度学习：LSTM、GRU、ALSTM、Transformer、Localformer、GATs、TRA、TCN、TabNet、SFM、ADD、ADARNN、KRNN、Sandwich、HIST、IGMTF 等（对应 examples/benchmarks 下每个目录一份 workflow yaml）
- RL 学习框架（2022 年发布）与 high-freq 示例。

### 2.4 官方 workflow：qrun 一键跑完整流水线
官方推荐 `qrun configuration.yaml`，用一份 yaml 定义 data→dataset→model→record 全流程：
```yaml
qlib_init:
    provider_uri: "~/.qlib/qlib_data/cn_data"
    region: cn
market: &market csi300
...
task:
    model:
        class: LGBModel
        module_path: qlib.contrib.model.gbdt
        kwargs: { loss: mse, learning_rate: 0.0421, max_depth: 8, num_leaves: 210, ... }
    dataset:
        class: DatasetH
        module_path: qlib.data.dataset
        kwargs:
            handler:
                class: Alpha158
                module_path: qlib.contrib.data.handler
            segments: { train: [...], valid: [...], test: [...] }
    record:
        - { class: SignalRecord, module_path: qlib.workflow.record_temp }
        - { class: PortAnaRecord, module_path: qlib.workflow.record_temp,
            kwargs: { config: *port_analysis_config } }
```
执行 `qrun configuration.yaml` 即完成：数据加载/处理/切片 → 模型训练推理 → 信号分析 + 回测。

### 2.5 回测（内置，无需 RD-Agent）
- **TopkDropoutStrategy**（qlib.contrib.strategy.strategy）——官方标准策略：每日持有 top-k 标的、定期换仓（n_drop）。
- **PortAnaRecord** + backtest 配置：可设 start/end、account、benchmark、手续费/涨跌停（limit_threshold）、滑点等。
- 支持 rolling 思路：官方多频/workflow 示例（workflow_config_lightgbm_*.yaml）通过 train/valid/test segments 分段 + SignalRecord 逐日打分，配合策略做滚动式评估；另有 "Online serving and automatic model rolling" 能力（2021 年发布）。
- 内置指标：IC / ICIR / Rank IC / Rank ICIR / Annualized Return / Information Ratio / Max Drawdown（见 benchmarks 页）。

### 2.6 因子评估
benchmarks 页给出标准评估方式：(a) alpha 与未来收益的相关系数；(b) 基于 alpha 构建组合评估总收益。指标定义见 qlib.readthedocs component/report。

## 3. 因子挖掘相关替代/开源项目

### 3.1 Microsoft RD-Agent（Qlib 官方配套，最直接）
- **R&D-Agent-Quant**（arXiv 2505.15155）：多 agent 框架做"数据为中心因子 + 模型联合优化"，在 Qlib 上跑。这正是"因子挖掘"最对口的官方方案。
- 定位：LLM 驱动的自动化 R&D，支持量化因子挖掘、因子+模型联合优化、从研究报告挖因子。
- **注意**：RD-Agent 就是需要额外安装的复杂度；如果只想"轻量跑因子 + 回测"，直接用 Qlib 内置 Alpha158/360 + LGBModel/MLP + qrun 即可，无需 RD-Agent。

### 3.2 AlphaFactory（非官方，GitHub 搜索同名）
- GitHub 搜索 "AlphaFactory" 存在多个同名仓库，其中与量化相关的主要是"A 股市场端到端 AI 因子挖掘平台，含五条并行挖掘通道"（Multi-Asset ML Alpha Factory / China A-share factor mining platform）等社区项目。
- 规模/维护程度参差，非单一权威项目；作为社区替代可参考，但成熟度低于 Qlib 官方路线。
- **注意**：用户提到的"deepseek AlphaFactory"未检索到对应官方仓库——DeepSeek 公开生态中未见同名官方 AlphaFactory 项目；建议以社区同名项目为参考，或采用 Qlib + RD-Agent 的官方路线。

### 3.3 其他值得关注的因子/alpha 项目
- Qlib 自带：**Alpha158 / Alpha360 特征集**、表达式引擎（可自定义公式化 alpha，见 advanced/alpha "Building Formulaic Alphas"）。
- 社区：各类 factor mining repo（如基于 qlib 的 alpha 表达式搜索、AutoAlpha/因子表达式进化等），但无统一权威库。

## 4. 关键结论摘要
- Qlib 完全可独立（不装 RD-Agent）跑通"下载数据 → Alpha158/360 特征 → LightGBM/MLP/深度模型 → qrun rolling 回测 → 指标评估"。
- 开箱即用点：内置数据集（cn/us）、Alpha158(158)/Alpha360(360) 特征、大量内置模型、qrun workflow、TopkDropoutStrategy 回测、IC/IR/回撤指标。
- 若需"自动化因子挖掘"，首选官方 **RD-Agent**（与 Qlib 深度集成）；"deepseek AlphaFactory"无权威官方仓库，AlphaFactory 同名社区项目可作为补充参考。
