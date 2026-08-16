# R-202 FinRobot 框架调研

> 调研日期：2026-08-12
> 来源：GitHub AI4Finance-Foundation/FinRobot 官方 README 及文档（真实抓取）
> 仓库：https://github.com/AI4Finance-Foundation/FinRobot
> 论文：FinRobot (arXiv:2405.14767)、ICAIF 2024 多篇

## 一、定位

FinRobot 是 **AI4Finance Foundation** 推出的**面向金融应用的 AI Agent 平台（多 Agent + LLM）**，超越 FinGPT 的单模型思路，统一整合 **LLM、强化学习、量化分析** 三类 AI 技术，用于：
- 投资研究自动化
- 算法交易策略
- 风险评估

核心形态 = **多 Agent 权益研究平台（Multi-Agent Equity Research）**，由一个 Lead Agent（编排/任务路由）调度多个专门子 Agent。

## 二、架构与技术栈

### Agent 体系（9 个 Agent）
- 1 个 **Lead Agent**（编排与任务路由）
- 5 个角色子 Agent：**Data → Analysis → Modeling → Synthesis → Report**（数据、分析、建模、综合、报告生成）
- 3 个 **辩论 Agent**：Bull（多方）/ Bear（空方）/ Judge（裁判）

### 设计原则（重要）
> **Numbers are code-calculated. Narratives are LLM-assisted. Every output is provenance-tracked.**
> 即"确定性金融计算 与 LLM 叙述严格分离"——所有财务数字（DCF、DDM、LBO、WACC、可比公司、蒙特卡洛）由**纯 Python 计算算子**生成，LLM 只做推理、综合、解释和报告写作。数值有完整可追溯来源。

### 技术栈（三层）
| 层 | 内容 |
|----|------|
| Agent 运行时 | 9 agents + 7 条研究流水线（公司研究、DCF、comps、LBO、DDM、盈利、IC memo） |
| 确定性计算 | 30 个纯 Python 算子 + 7 个协调器（估值/WACC/蒙特卡洛/建模） |
| 数据基础设施 | 7 个带故障切换的数据源：FMP、Finnhub、yfinance、SEC EDGAR、Adanos、NewsAggregator、FX |
| 产品技术栈 | **PydanticAI + FastAPI + SQLite + React 19 + Vite 6 + Zustand + Tauri/Rust + Recharts** |

- 全栈代码约 **18.4 万行**（Python 后端 + React/Tauri 桌面前端 + Rust shell + 测试）
- 提供 **FinRobot Desktop**（macOS Apple Silicon 原生桌面应用，v0.1.0）

### 传统 FinRobot 主包（finrobot/ 目录）
- agents / data_source / functional 三块
- data_source：finnhub、finnlp、fmp、sec、yfinance 工具
- functional：analyzer、charting、coding、quantitative、reportlab、text
- 底层用 **AutoGen 类多 Agent 框架**（配置 OAI_CONFIG_LIST，需 OpenAI API key）
- 依赖：Python 3.10、需配置 OpenAI key + Finnhub/FMP/SEC key

## 三、A股支持情况

**原生偏向美股，A股支持薄弱**：
- 官方数据源/示例全部聚焦 **美股**（NVDA、MSFT、COP、TSLA、META 等美股权益研究报告）
- 数据源为 FMP、Finnhub、yfinance、SEC EDGAR 等，**均为美股/全球市场**，无 Tushare/Akshare 等 A股数据源集成
- 文档、教程、Desktop 产品均面向美股权益研究
- **结论**：FinRobot 当前主要面向美股权益研究与估值报告，A股支持需自行扩展数据源与适配，开箱即用程度低。

## 四、学习成本

- **较高**：涉及多 Agent 编排、LLM API 配置（OpenAI key）、数据源 key 配置、Pydantic/FastAPI/前端技术栈（Desktop 版含 React/Tauri）。
- 需掌握：Python、LLM/Agent 概念、AutoGen 类框架、财务估值（DCF/DDM/LBO/WACC）。
- 官方提供 tutorials_beginner（agent_annual_report、agent_fingpt_forecaster）与 tutorials_advanced（agent_trade_strategist、opt_smacross 等）多个 Notebook 教程，上手路径清晰但有一定深度。

## 五、与微盘股因子轮动/交易的关系

- FinRobot 定位是 **投研分析/权益研究报告自动化**（分析+估值+报告），**不是交易执行/因子轮动框架**。
- 虽提及"算法交易策略"与 Trading Strategies Agent（trade_strategist），但主体能力是研究型多 Agent 分析，非因子回测与轮动引擎。
- 若要做微盘股因子轮动，FinRobot 不适合作为主引擎，更适合作为"研究/报告生成辅助层"，且需自行接入 A股数据。

## 六、关键数据速览

- 许可：Apache-2.0
- 安装：`pip install finrobot` 或 `git clone` + `pip install -e .`（Python 3.10）
- 关键依赖配置：OAI_CONFIG_LIST（OpenAI key）、config_api_keys（Finnhub/FMP/SEC key）
- 配套生态：FinGPT（金融 LLM）、FinRL / FinRL-X（DRL 交易）
- 定位对比：FinRL = DRL 交易/组合；FinRobot = LLM 多 Agent 投研分析；FinGPT = 金融大模型

## 七、总结

FinRobot 是 AI4Finance 的**多 Agent + LLM 权益研究平台**，擅长把"数据抓取 → 财务分析 → 估值建模 → 多空辩论 → 研究报告生成"流水线自动化，数值计算与 LLM 叙述严格分离、可追溯，是高质量投研报告工具。但**主要面向美股、A股支持薄弱**，且定位为研究分析而非交易/因子轮动执行，学习成本偏高。对微盘股因子轮动场景参考价值有限，更适合作为研究辅助而非主引擎。
