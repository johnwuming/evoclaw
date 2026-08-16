# R-202 RD-Agent 调研报告

## 1. 定位

**RD-Agent（Microsoft Research 开源，microsoft/RD-Agent）**：一个"数据驱动的 AI"自动化研发（R&D）多智能体框架。方法论核心为 **'R'（Research，提出新想法）+ 'D'（Development，实现）** 两大组件，用 LLM 自动化"提出想法→实现→评估→再提出"的自循环。

针对量化金融，RD-Agent(Q)（论文 arXiv:2505.15155，NeurIPS 2025 录用）是**首个数据为中心的多智能体框架**，通过"因子-模型联合优化"（factor-model co-optimization）自动化量化策略的全栈研发。官方宣称：成本 <$10 时，ARR 约为基准因子库的 **2 倍**，且因子数减少 **70% 以上**。

## 2. 架构（基于 Qlib）

- **底层回测/研究框架：Qlib（Microsoft 开源，github.com/microsoft/qlib）**——RD-Agent 的因子/模型自循环全部跑在 Qlib 之上。
- 多个场景（scenario）：
  - `rdagent fin_factor`：因子进化（Qlib 自循环因子提出与实现）
  - `rdagent fin_model`：模型进化（Qlib 自循环模型提出与实现）
  - `rdagent fin_quant`：因子+模型**联合进化**
  - `rdagent fin_factor_report`：从财报/研报自动抽取因子
  - 另含 general_model（论文→模型）、data_science（Kaggle/医学）、llm_finetune（FT-Agent）等场景
- **多智能体**：Research Agent（提想法）+ Development Agent（写代码实现）+ 评估/反馈回路。
- **数据格式：Qlib 标准格式（bin 文件，qlib dump）**；需配置因子、股票池、训练/回测区间。
- **LLM 后端**：LiteLLM 统一接入，支持 OpenAI / Azure / **DeepSeek（官方支持）** 等；需 `CHAT_MODEL` + `EMBEDDING_MODEL`（如 BAAI/bge-m3）。支持 reasoning 模型（需设 REASONING_THINK_RM=True）。

## 3. 运行环境要求（相比 AlphaEvolve 更重）

- **必须安装 Docker**（绝大多数场景依赖，README 明确要求）。
- Python 3.10 / 3.11（CI 验证过）。
- `pip install rdagent`（PyPI）或源码 `make dev`。
- 需要同时配置 Chat 模型和 Embedding 模型。
- 需运行 `rdagent health_check` 验证环境。
- 数据准备较繁琐：Qlib 数据 dump + 因子配置 + 区间划分。

## 4. 是否支持 A 股

**原生支持**。Qlib 本身提供中国 A 股数据工具（`get_data` 可下载 CN 数据，qlib 内置中国 A 股数据接口与因子库），RD-Agent 跑在 Qlib 之上，天然适配 A 股。这是相对 PWB 数据生态（美股为主）的优势。

## 5. 学习成本

- **较高**。需掌握：
  1. Qlib 数据格式与 dump 流程；
  2. Docker 环境；
  3. 多智能体/场景配置（LLM、embedding、因子、区间）；
  4. 因子的"提出-实现-回测"自循环概念。
- 文档齐全（readthedocs），但上手门槛显著高于 AlphaEvolve 单文件配置。

## 6. 关键结论

- RD-Agent = **Microsoft 出品、基于 Qlib 的因子+模型联合进化的多智能体框架**，功能强、体系完整、原生支持 A 股。
- 依赖重（Docker + Qlib + 双 LLM），学习曲线陡。
- 参考链接：
  - GitHub：https://github.com/microsoft/RD-Agent
  - RD-Agent(Q) 论文：https://arxiv.org/abs/2505.15155
  - 技术报告：https://aka.ms/RD-Agent-Tech-Report
  - 文档：https://rdagent.readthedocs.io/

## 7. 与 AlphaEvolve 对比小结

| 维度 | AlphaEvolve（pwb 交易版） | RD-Agent(Q) |
|---|---|---|
| 出品方 | Google DeepMind（移植版社区维护） | Microsoft Research |
| 回测框架 | **Backtrader** | **Qlib** |
| 数据格式 | PWB / HuggingFace 数据集（Feather） | Qlib bin |
| A 股 | 需自备数据适配 | **原生支持** |
| 无 GPU / 15G 内存 | ✅ 可跑（API 或 phi-2 本地） | ✅ 可跑（LLM API + CPU），但需 Docker |
| 学习成本 | 低（单 config + seed 策略） | 高（Docker+Qlib+双 LLM） |
| 依赖复杂度 | 轻（无 qlib） | 重 |
| 因子进化 | 支持（策略级，非因子库级） | 因子+模型联合优化（更强） |
