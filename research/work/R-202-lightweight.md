# R-202 调研：轻量回测生态（PyBroker / backtesting.py / vectorbt）

> 调研日期：2026-08-12｜数据来源：GitHub README（edtechre/pybroker、kernc/backtesting.py、polakowo/vectorbt）

## 1. PyBroker（backtrader 的现代替代）
- GitHub: edtechre/pybroker｜`pip install -U lib-pybroker`｜Python 3.10+，Windows/Mac/Linux。
- 定位：**面向机器学习策略的 Python 回测框架**，数据源 + 回测 + ML 一体化。
- 特性：
  - 核心引擎基于 **NumPy + Numba**（超快）。
  - 多标的规则与模型策略；支持 **Walkforward Analysis（滚动前推）** 训练+回测，模拟真实交易。
  - **随机 Bootstrap 指标**（更可靠的回测统计），并行计算，数据/指标/模型缓存。
  - 数据源：**Alpaca、Yahoo Finance、AKShare（A股）**，或自定义数据源。
  - `pybroker.model('my_model', train_fn, ...)` 注册 ML 模型 + 预测驱动交易。
- A股：✅ 经 AKShare 支持。
- 无 GPU：✅ 纯 CPU。
- 学习成本：低-中（简洁 Strategy / exec_fn 风格，文档含 10+ notebook，有中文文档）。

## 2. backtesting.py（kernc）
- `pip install backtesting`｜极简、单标的轻量回测，Bokeh 交互可视化。
- `Backtest(data, Strategy, commission)` + `bt.run()` + `bt.plot()`，返回完整统计 Series。
- 特性：超快执行、内置 **SAMBO 优化器**（参数网格搜索）、可组合基础策略库、指标库无关（BYO）、支持任意 OHLC(V) 标的。
- 定位：**最简单上手的规则型单标的回测**；不含内置数据源/A股接入（需自备 DataFrame），无内置 ML 训练框架。
- 无 GPU：✅ 纯 CPU。学习成本：低。

## 3. vectorbt（polakowo/vectorbt）
- `pip install -U vectorbt`（可选 `[rust]`/`[full]`）。开源社区版（**Apache 2.0 + Commons Clause**：免费可用但不可直接出售该软件本身）。
- 定位：**向量化（非逐 bar 循环）大规模回测引擎**——把上千配置打包进 NumPy 数组，用 **Numba + 可选 Rust** 加速，把数小时网格搜索压到秒级。
- 特性：pandas 原生 API + vbt accessor、多资产广播、参数扫描 heatmap、组合/交易/回撤分析（QuantStats 集成）、TA-Lib/Pandas TA 指标、walk-forward 优化 + ML 标签生成、Plotly 交互可视化、AI agent 友好（可组合 API）。
- 数据源：内置 YFData（Yahoo）等；A股需自备数据（Yahoo 有 A股 ticker 后缀，可配合 AKShare 喂数据）。
- 无 GPU：✅ 纯 CPU（Numba JIT）。学习成本：中（向量化 API 与逐 bar 思路不同，但文档/示例丰富）。

## 4. 对比结论
| 维度 | PyBroker | backtesting.py | vectorbt |
|---|---|---|---|
| 定位 | ML 策略+数据+回测一体 | 最简规则型单标的 | 大规模向量化网格扫描 |
| 引擎 | NumPy+Numba | 事件循环(极简) | NumPy+Numba(+Rust) |
| 内置数据源 | Alpaca/Yahoo/AKShare | 无(自备) | Yahoo/自备 |
| A股 | ✅ AKShare | 手动 | 手动 |
| ML 训练 | ✅ Walkforward | ❌ | ⚠️ 标签/扫描 |
| 学习成本 | 低-中 | 低 | 中 |
| 无 GPU | ✅ | ✅ | ✅ |

- 组合建议：**PyBroker**（含 ML+Walkforward+A股 AKShare）最贴合"数据+回测+机器学习"需求；**backtesting.py** 适合快速验证简单规则；**vectorbt** 适合大规模参数扫描/网格研究。三者都轻量、纯 CPU，可作为 Qlib 之外的快速原型层。
