# R-202 调研：Microsoft Qlib 原生 AutoML / 模型集成（auto workflow / Rolling / Ensemble）

> 调研日期：2026-08-12｜数据来源：GitHub README + qlib.readthedocs（workflow / online serving 组件）

## 1. 定位
Qlib 是微软开源的 **AI 量化投资平台**，覆盖从"探索想法到生产落地"全链路：数据处理 → 因子挖掘 → 模型训练 → 回测 → 在线服务。支持监督学习、市场动态建模（概念漂移）、强化学习三大范式。当前正被 **RD-Agent**（LLM 驱动的自动化 R&D）接管自动化部分。

## 2. 原生 AutoML / 自动研究流程
- **qrun**：Qlib 核心的"一键自动量化研究工作流"。用户只需写一个 YAML 配置（data→model→dataset→record），qrun 自动完成建数据集、训练、推理、回测、评估。配置含 qlib_init、task（model/dataset/record）、port_analysis_config 等。
- **Recorder 实验管理**：每次 execution 完整追踪训练/推理/评估产生的信息与工件（artifacts）。
- 数据集侧内置 **Alpha158 / Alpha360** 等因子集（handler），可直接当作基准因子库。

## 3. 模型集成 / Rolling（自动滚动）
- 内置 **DoubleEnsemble**、**AverageEnsemble**、**Rolling** 等集成/滚动机制：
  - `qlib.model.ens.ensemble.AverageEnsemble` / `ModelEnsemble`：多模型预测平均/加权集成（在线服务 prepare_signals 默认即用 AverageEnsemble）。
  - **Rolling**：时间滚动训练（TRA/rolling train），配合 OnlineManager 实现**自动模型滚动（automatic model rolling）**——每 routine 重训/更新在线模型。
  - DoubleEnsemble：样本与特征双重集成，专为金融噪声设计。
- 在线服务组件（OnlineManager / OnlineStrategy / Trainer / DelayTrainer）：管理随市场变化的"在线模型"，支持 Simulation+Trainer 的历史仿真回测与 Online+Trainer 的真实例行。适合作为"更简单的因子挖掘替代"——你只需 YAML 换因子集和模型，跑 qrun 即得 IC/回测报告。

## 4. A股支持：✅ 原生支持
`region: cn`（China-stock mode），官方示例默认 csi300 / SH000300 基准，提供中文数据。数据可用官方脚本/社区数据源（chenditc investment_data，注意官方数据集暂因数据安全策略临时停用，需用社区源或自行 Yahoo 采集）。

## 5. 无 GPU 能否跑：✅ 可以
LightGBM（LGBModel）等 GBDT 模型纯 CPU 可跑；深度学习模型（Transformer 等）可选 GPU 但不是必需。安装 `pip install pyqlib`（Python 3.8–3.12，建议 conda 环境）。

## 6. 学习成本：中高（但自动化程度高）
- qrun + YAML 上手快（"最简单的因子挖掘替代"）；但深度自定义需要理解 DataHandler / DatasetH / init_instance_by_config / workflow_by_code 等组件化设计。
- 官方文档完整（readthedocs + notebook tutorial + workflow_by_code 示例）。

## 7. 结论 / 适用性
- **非常适合作为"更简单的因子挖掘替代"**：内置 Alpha158/Alpha360 因子集 + 预训练基准模型（LightGBM/GBDT）+ qrun 一键自动化 + IC/回测标准报告 + 原生 A股 + CPU 可跑。
- 比 TradingAgents 更"数值化、可复现、规模化"，是真正的量化研究底座。
- 注意：当前自动化/因子挖掘方向官方重心已转向 RD-Agent；Qlib 本身 v0.9.x 更新趋缓，但作为稳定基建仍可靠。
