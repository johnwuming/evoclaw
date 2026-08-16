# R-202 AlphaEvolve 调研报告

> ⚠️ **重要更正**：任务描述称 AlphaEvolve 为"DeepSeek 开源因子进化框架"，**此说法有误**。经查证，AlphaEvolve 是 **Google DeepMind** 2025 年的研究项目（技术报告 arXiv:2506.13131，作者 Novikov et al.）。DeepSeek 并未开源 AlphaEvolve。请勿将两者混淆。

## 1. 定位

AlphaEvolve 是 Google DeepMind 发布的 **Gemini 驱动的编码智能体（coding agent）**，用于科学和算法发现——通过"进化式"方式让 LLM 反复改写/优化程序代码（算法），在数学（矩阵乘法、圆填充）、GPU kernel、信号处理等领域取得突破。它本身**不是**为量化因子量身定制的框架，而是通用的"LLM + 进化算法"引擎，被社区移植应用到交易策略/因子发现。

## 2. 技术栈

官方 DeepMind 仓库 `google-deepmind/alphaevolve_results` **只放出结果 notebook（Colab）与验证代码，未放出可运行的进化引擎代码**。

社区开源实现主要有两个：

### A. openevolve（通用引擎，algorithmicsuperintelligence/openevolve）
- ~6,900 stars，Apache-2.0，Python（pip install openevolve），Python 3.10+
- 核心算法：**MAP-Elites（质量-多样性）+ 岛屿架构 + LLM 集成**
- LLM 后端：任何 OpenAI 兼容 API（OpenAI / Gemini / Claude Code CLI / Ollama·vLLM 本地模型 / OptiLLM 代理）
- 定位：通用算法进化（函数优化、符号回归、排序、GPU kernel），**非量化专用**
- 评估器由用户自定义 evaluator 函数

### B. pwb-alphaevolve（交易策略版，paperswithbacktest/pwb-alphaevolve）
- MIT 协议，Python ≥ 3.10
- **回测框架：Backtrader（pwb-backtrader）**——注意：**不使用 qlib / qlisp**
- **数据格式：Papers-With-Backtest 数据生态**——从 HuggingFace 加载 PWB 数据集（如 `paperswithbacktest/Stocks-Daily-Price`），缓存为 Feather；零配置加载器（pwb_toolbox）
- **LLM 引擎：OpenAI o3 结构化输出（需 OPENAI_API_KEY）；也支持本地 LLM**（transformers + bitsandbytes 加载 phi-2，或转发到 OpenAI 兼容本地服务器）
- 进化机制：异步 controller + **SQLite hall-of-fame** + 可选 MAP-Elites niches + 多分支变异（分别优化 sharpe/calmar/cagr）+ 提示词遗传进化（PromptGenome）
- 策略形态：seed 策略文件内嵌 **EVOLVE-BLOCK 标记**，LLM 对标记块做 diff/patch 变异
- 评估：Backtrader walk-forward，JSON KPI（Sharpe、CAGR、Calmar、最大回撤）
- 可视化：Streamlit GUI
- 依赖：pwb-toolbox、pwb-backtrader、openai≥1.0、tqdm/pandas/numpy/pydantic

## 3. 是否支持 A 股

- 原生不面向 A 股。PWB 数据生态以美股/全球日线 OHLCV 为主。
- 但框架是**标的不敏感**的：评估器/数据加载器独立，只要通过 pwb_toolbox 加载任意数据集（含 A 股 OHLCV，或自备 CSV/Feather）即可适配 A 股。
- 结论：**可改造支持 A 股**，但非开箱即用，需自己提供 A 股数据并匹配 PWB 数据接口。

## 4. 能否在无 GPU、15G 内存环境运行

**可以。**
- 默认模式（OpenAI o3 API）：计算主体是 LLM API 调用 + CPU 回测，**完全不需要 GPU**，内存开销很小（pandas/Backtrader 处理日线数据）。
- 本地模式：`microsoft/phi-2`（2.7B 参数）配合 bitsandbytes 量化加载，**远小于 15G 内存**，可在 CPU 上跑推理。
- openevolve 亦支持 Ollama/vLLM 本地小模型，CPU 可运行。
- 唯一前提：本地跑需有可用的 LLM（API 或本地小模型）；否则进化引擎无法工作。

## 5. 学习成本

- **较低**。核心只需：
  1. 准备一个 seed 策略文件（含 EVOLVE-BLOCK 标记）+ 配置 config.py（tickers、回测区间、排序指标）；
  2. 配好 LLM 后端；
  3. 跑 `python scripts/run_example.py` 或 Streamlit GUI。
- 无需理解 MAP-Elites / qlib 细节即可上手，配置集中在单一 config 文件。
- 对不熟悉 Backtrader / PWB 数据生态者有小学习曲线，但远低于 RD-Agent。

## 6. 关键结论

- AlphaEvolve 是 **DeepMind 通用"编码智能体 + 进化算法"**框架，非 DeepSeek、非量化专用；交易版（pwb-alphaevolve）为其移植。
- 技术栈极简：**Backtrader 回测 + PWB 数据集 + 一个 LLM + SQLite**，无 qlib 依赖。
- 无 GPU / 小内存可跑，本地小模型（phi-2）即可。
- A 股需自备数据、做轻量适配。
- 参考链接：
  - 官方技术报告：https://arxiv.org/abs/2506.13131
  - DeepMind 官方结果仓库：https://github.com/google-deepmind/alphaevolve_results
  - 开源通用实现：https://github.com/algorithmicsuperintelligence/openevolve
  - 交易策略版：https://github.com/paperswithbacktest/pwb-alphaevolve
