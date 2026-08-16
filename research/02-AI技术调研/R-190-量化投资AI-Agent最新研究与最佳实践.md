# 量化投资AI Agent最新研究与最佳实践调研报告

> **报告编号**: R-190  
> **调研时间**: 2026年8月  
> **适用对象**: 量化投资团队（A股小市值策略，LLM因子挖掘，本地CPU执行）  
> **报告字数**: 约11,000字

---

## 目录

1. [执行摘要](#一执行摘要)
2. [AI量化最新研究（2024-2026）](#二ai量化最新研究2024-2026）
3. [开源量化AI框架对比](#三开源量化ai框架对比）
4. [行业最佳实践](#四行业最佳实践）
5. [对我们系统的具体建议](#五对我们系统的具体建议）
6. [应避免的常见坑](#六应避免的常见坑）
7. [推荐学习资源和开源项目](#七推荐学习资源和开源项目）
8. [参考文献](#八参考文献）

---

## 一、执行摘要

本报告系统调研了2024-2026年量化投资领域AI Agent的最新研究进展和最佳实践，旨在为我们的自进化量化系统（A股小市值、月频调仓、20只持仓、DeepSeek V4 Flash因子挖掘、本地CPU执行、5205只A股数据）提供参考。

**核心发现：**

1. **LLM因子挖掘已从概念验证进入学术认可阶段**。微软RD-Agent(Q)被NeurIPS 2025接收，以少于70%的因子实现2倍年化收益，标志着这一方向的技术可行性得到验证。AlphaAgent提出抗因子衰减机制，在CSI500上表现突出。

2. **开源框架生态日趋成熟**。Qlib+RD-Agent组合构成了从因子挖掘到回测验证的完整工具链，FinRL在强化学习方向保持活跃，vectorbt在快速回测上优势明显。

3. **A股小市值策略面临拐点**。2024年初微盘股闪崩后，小市值策略拥挤度达到历史高位。2025年量化指增产品平均收益45%，但纯小市值alpha大幅衰减。需要从"纯小市值"向"小市值+多因子增强"转型。

4. **对于我们的条件（CPU本地、10万资金、月频），务实路径是**：以Qlib为基础设施，用DeepSeek+RD-Agent做因子假设生成，严格过拟合控制（Walk-forward+置换检验），策略从红利低波起步，逐步叠加LLM挖掘的因子。

---

## 二、AI量化最新研究（2024-2026）

### 2.1 LLM在因子挖掘中的应用

#### 2.1.1 微软RD-Agent(Q)：里程碑式突破

RD-Agent是微软研究院开源的工业级R&D自动化Agent框架，其量化金融专项应用RD-Agent(Q)是当前最受瞩目的LLM因子挖掘系统。

**核心论文**：*"R&D-Agent-Quant: A Multi-Agent Framework for Data-Centric Factors and Model Joint Optimization"*（arXiv:2505.15155），Xu Yang等，微软研究院，**NeurIPS 2025接收**。

**技术架构**：RD-Agent将量化研发流程抽象为两个迭代阶段：

- **Research阶段**：Research Agent基于领域先验提出因子假设，动态设定目标对齐的提示词，将假设映射为具体任务
- **Development阶段**：Co-STEER代码生成Agent将任务转化为可执行的因子代码，在Qlib上运行真实回测
- **Feedback阶段**：通过多臂赌博机调度器（Multi-Armed Bandit Scheduler）进行自适应方向选择，指导下一轮迭代

**实验结果**：
- 成本低于10美元的情况下，使用比基准因子库少70%以上的因子
- 实现约**2倍年化收益率（ARR）**
- 优于当时最先进的深度时间序列模型
- 因子-模型联合优化在预测精度和策略鲁棒性间取得良好平衡

**最新功能**（2026年中）：已扩展至自动量化工厂（Automatic Quant Factory）、数据挖掘Agent、研究Copilot、Kaggle Agent等场景。在MLE-bench上以35.1%奖牌率位居榜首，是当前最强ML工程Agent。

**关键启示**：RD-Agent证明了LLM可以端到端地完成"提出假设→生成代码→回测验证→迭代优化"的全流程。但它仍依赖强大的底层LLM（推荐o3/GPT-4级别），且样本外长期有效性缺乏验证。

#### 2.1.2 AlphaAgent：抗因子衰减的因子挖掘

**论文**：*"AlphaAgent: LLM-Driven Alpha Mining with Regularized Exploration to Counteract Alpha Decay"*（arXiv:2502.16789），Ziyi Tang等，2025年2月。

**核心创新**——三个正则化机制：
1. **原创性约束**：基于抽象语法树（AST）的相似度度量，确保新因子与已有因子有足够差异
2. **假设-因子对齐**：LLM评估市场假设与生成因子间的语义一致性
3. **复杂度控制**：基于AST的结构约束，防止过拟合的复杂因子构造

**实验结果**：在中国CSI500和美国S&P500过去四年中，AlphaAgent显著优于传统遗传规划方法和基础LLM方法，展现出优异的抗因子衰减能力。

**对我们的意义**：AlphaAgent的三个机制可以直接借鉴——在我们的因子挖掘流程中，应加入因子原创性检查、假设-因子一致性验证和复杂度约束。

#### 2.1.3 Chain-of-Alpha：双链因子挖掘框架

**论文**：*"Chain-of-Alpha: Unleashing the Power of Large Language Models for Alpha Mining in Quantitative Trading"*，2025年。

该论文提出双链架构：Factor Generation Chain（因子生成链）和Factor Validation Chain（因子验证链），两条链协同工作。生成链负责产出新因子假设，验证链独立审查因子的有效性和经济逻辑。

#### 2.1.4 FactorMAD：多智能体辩论框架

**论文**：发表于ACM（doi:10.1145/3768292.3770377），提出基于LLM的多智能体辩论范式挖掘alpha因子。多个Agent分别扮演因子提出者、质疑者和裁判，通过辩论提升因子质量。

#### 2.1.5 LLMFactor：从新闻提取可解释因子

**论文**：*"LLMFactor: Extracting Profitable Factors through Prompts for Explainable Stock Movement Prediction"*，Meiyun Wang等，**ACL 2024 Findings**。

提出顺序知识引导提示（SKGP）方法，从金融新闻中提取可解释的因子——不同于简单的情感分析，LLMFactor能识别具体驱动因素（如"新产品发布""管理层变动"），转化为可量化的alpha信号。

#### 2.1.6 CN-Buzz2Portfolio：中国市场LLM基准

**论文**：*"CN-Buzz2Portfolio: A Chinese-Market Dataset and Benchmark for LLM-Based Macro and Sector Asset Allocation"*（arXiv:2603.22305），2026年3月。

这是目前最系统的**中文市场**LLM金融评测基准。覆盖2024-2025年，评测了9个主流LLM在中文金融决策中的表现。关键发现：不同LLM在中文金融理解上差异巨大，ETF层面配置比个股选择更适合LLM能力范围。

### 2.2 FinGPT与金融大模型生态

**FinGPT**（AI4Finance Foundation）是首个开源金融大语言模型，核心论文arXiv:2306.06031。采用数据中心化方法，提供自动数据采集流水线，支持LoRA/QLoRA轻量微调（单RTX 3090成本<$300）。在金融情感分析基准上超越GPT-4，但项目2024年后更新明显放缓。

**BloombergGPT**（2023年3月）：500亿参数，训练成本约267万美元，完全闭源，被视为金融LLM的奠基工作但实用性受限。

**后续值得关注的金融LLM**：FinRobot（多Agent平台）、CFGPT（中文金融LLM）、InvestLM（香港大学）。信达证券2025年研究报告开创性地引入DeepSeek优化价量因子，构建"优化-验证-再迭代"框架。

### 2.3 强化学习在组合优化中的进展

#### 2.3.1 总体趋势

2024-2026年，RL在量化金融中的研究从"RL能否超越均值-方差"转向更务实的方向：动态仓位调整、风险控制、交易执行优化、市场状态切换。

#### 2.3.2 2026年重要论文

- **AlphaZeroBeta**（2026.7）：将AlphaZero自博弈思想引入市场中性组合
- **SciPhy RL**（Igor Halperin, 2026.7）：物理启发的动态组合优化
- **FPILOT**（2026.5）：推理时优化RL交易代理，显著提升性能
- **EvoNash-MARL**（2026.4）：多智能体RL框架用于中期股票配置

#### 2.3.3 FinRL框架

FinRL（GitHub星标10,000+）是最活跃的金融RL框架，已演进为FinRL-X（AI原生、模块化、面向生产）。支持PPO、SAC、DDPG、A2C、TD3等算法。2025年FinRL竞赛引入DeepSeek作为核心模型。

**RL的实际部署挑战**：过拟合风险、非平稳性、交易成本建模、可解释性差、样本效率低。RL最适合的场景是**交易执行优化**（目标明确、环境可模拟、反馈迅速），而非直接用于投资组合选择。

### 2.4 图神经网络选股

GNN选股的核心价值在于捕捉股票间的关联结构（供应链、行业归属、因子共暴露等）。2024-2025年的重要进展包括：

- **多关系异构图**成为主流（*"Structure Over Signal"*, 2025）：单一关系图不足以捕捉全部信息
- **GNN+Mamba/Transformer混合架构**（*"Graph-Mamba for Stock Price Prediction"*, 2024-2025）
- **GRU-PFG**（2024.11）：从传统Barra因子中提取股票关联，用GNN增强——适合已有因子框架的团队
- **"Evaluating Financial Relational Graphs"**（2024.9）：核心启示——**图结构的金融逻辑比GNN模型架构更重要**，不是所有"图"都能带来alpha

### 2.5 另类数据+LLM生成文本因子

文本因子的Alpha衰减速度和实用性因信息源差异巨大：

| 文本因子类型 | Alpha衰减速度 | 容量 | 实用性评级 |
|---|---|---|---|
| 研报情感因子 | 中（日级） | 大 | ★★★★★ |
| 公告事件因子 | 慢（日级） | 大 | ★★★★★ |
| 新闻情感因子 | 快（分钟级） | 中 | ★★★★ |
| 社交媒体因子 | 极快（秒级） | 小 | ★★★ |

**中文金融文本的特殊挑战**：隐式情感表达（"有待观察"通常偏负面）、政策文本解读至关重要、数据源多需付费、合规限制。

**安全警示**：2026年论文*"Adversarial News and Lost Profits"*揭示了通过篡改新闻标题操纵LLM交易系统的风险，实际部署需多源交叉验证。

---

## 三、开源量化AI框架对比

### 3.1 核心框架总览

| 框架 | 星标 | 类型 | AI支持 | A股 | 实盘 | 维护 | 学习难度 |
|------|------|------|--------|-----|------|------|---------|
| **Qlib** | 15K+ | AI量化全流程 | ★★★★★ | ★★★★ | ★★ | ★★★★ | 高 |
| **RD-Agent** | 5K+ | LLM自动研发 | ★★★★★ | ★★★★ | ★ | ★★★★★ | 很高 |
| **FinRL** | 10K+ | RL量化交易 | ★★★★ | ★★ | ★★★ | ★★★★ | 中高 |
| **vectorbt** | 4.5K+ | 向量化回测 | ★★ | ★★ | ★ | ★★★★ | 中低 |
| **AKShare** | 11K+ | 数据接口 | - | ★★★★★ | - | ★★★★★ | 低 |

### 3.2 Qlib（微软）——我们的核心基础设施

Qlib是当前学术界和工业界结合最紧密的开源量化框架，覆盖从因子挖掘到回测的全链路。

**核心能力**：
- **Alpha158/Alpha360因子库**：开箱即用的因子集，涵盖量价、财务等多维度
- **Model Zoo**：包含LightGBM、Transformer、GATs、HIST、TFT等十余种模型
- **因子表达式引擎**：支持Ref/Mean/Std/Rank/Corr等时序运算，高性能并行计算
- **自定义模型**：继承基类→实现fit/predict→YAML配置注册，三步完成集成

**已知局限**：实盘支持薄弱、A股数据更新滞后（官方到2022年）、配置体系复杂、文档不足。

**对我们**：Qlib应作为因子计算和回测的核心引擎。我们已有的5205只A股K线+财务数据，可以通过Qlib的DataProvider接口注入。

### 3.3 RD-Agent（微软）——我们的因子挖掘利器

RD-Agent的量化场景底层依赖Qlib作为执行引擎，核心循环为：

```
假设生成（Research Agent）→ 代码实现（Co-STEER）→ Qlib回测 → 
反馈分析（MAB调度器）→ 知识积累 → 下一轮迭代
```

**与我们系统的契合度**：
- 原生支持A股（CSI300/CSI500），可扩展到全市场
- 已提供DeepSeek模型支持——与我们使用DeepSeek V4 Flash的计划高度契合
- LLM API成本是主要考虑因素，DeepSeek的低成本API是优势
- 安装门槛：`pip install rdagent`，需配置LLM API密钥

### 3.4 FinRL——RL探索方向的参考

FinRL提供完整的train-test-trade管道，但RL方法在实盘中面临过拟合、非平稳性、可解释性等严峻挑战。**建议我们暂时不将RL作为核心方法**，但关注其在交易执行优化方面的进展。

### 3.5 vectorbt——快速参数优化工具

vectorbt的核心优势是将数千个策略配置打包成NumPy数组，利用Numba JIT编译实现极速回测。适合大规模参数扫描和Walk-forward分析。社区版开源免费，PRO版提供Rust引擎。

### 3.6 其他值得关注的项目

- **NautilusTrader**（5K+星标）：Rust原生交易平台，"研究即生产"理念，适合未来追求实盘部署
- **AKShare**（11K+星标）：免费全面的A股数据接口，是我们数据层的补充
- **AKQuant**：同作者的Rust+Python回测框架，内置Walk-forward和因子表达式引擎

---

## 四、行业最佳实践

### 4.1 因子挖掘自动化流程

成熟的因子挖掘应遵循完整闭环：

```
因子假设 → 数据获取 → 因子计算 → 预处理 → 
有效性检验 → 因子合成 → 组合优化 → 回测验证 → 实盘跟踪
```

**因子预处理标准流程**：
1. **去极值**：MAD法（Median Absolute Deviation），比3σ更稳健
2. **标准化**：Z-Score或Rank秩标准化
3. **中性化**：行业中性化+市值中性化（回归取残差），消除风格暴露

**因子有效性检验标准**：

| 指标 | 合格标准 |
|------|---------|
| 月度IC均值 | >0.03有信号，>0.05有效 |
| IC_IR（IC信息比） | >0.5良好，>1.0优秀 |
| IC胜率 | >55%可接受，>60%稳健 |
| 多空年化收益 | >5%，t统计量>2 |
| 月换手率 | <50%为佳 |

### 4.2 回测注意事项

#### 4.2.1 A股回测的必须处理项

| 问题 | 正确做法 | 常见错误 |
|------|---------|---------|
| **涨跌停** | 涨停不可买入，跌停不可卖出 | 框架默认成交，收益虚高 |
| **停牌** | 停牌股剔除可交易池，复牌模拟跳价 | 按前日收盘假装收益为0 |
| **T+1** | 卖出仅限前一交易日及之前持仓 | 忽略限制，虚拟日内交易 |
| **幸存者偏差** | 使用Point-in-Time数据，包含退市股票 | 只回测现存股票 |
| **前视偏差** | 财务数据用报告期+发布延迟 | 使用了未来才公布的数据 |

**交易成本保守估算**：
- 买入：佣金万1~万3 + 滑点千1~千2 ≈ 万3~千3
- 卖出：佣金万1~万3 + 印花税万5 + 滑点千1~千2 ≈ 千1~千3
- **单次来回约千2~千4**，月频换手50%策略年成本约1.2-2.4%

#### 4.2.2 过拟合防范的四重保障

**第一重：严格的样本外检验**
- 训练集/验证集/测试集严格分离
- 测试集"只看一次"——看完不改策略

**第二重：Walk-Forward分析**
```
窗口1: 训练2015-2019 → 预测2020
窗口2: 训练2016-2020 → 预测2021
窗口3: 训练2017-2021 → 预测2022
窗口4: 训练2018-2022 → 预测2023
窗口5: 训练2019-2023 → 预测2024
```
OOS收益/IS收益>50%可认为有一定稳健性。

**第三重：蒙特卡洛置换检验**
将因子值随机打乱1000次构建IC零分布，真实IC不在95%置信区间外则因子可能无效。

**第四重：参数敏感性分析**
对参数做±20%、±50%扰动，稳健策略应表现为"参数高原"而非"参数尖峰"。

### 4.3 A股市场特殊性

#### 4.3.1 2024-2025年市场环境关键变化

- **微盘股危机**（2024年2月）：万得微盘股指数闪崩，量化基金单周回撤超15%，暴露了小市值策略的脆弱性
- **量化监管趋严**：限制量化高频交易，程序化交易报告制度建立——对月频策略影响较小
- **注册制深化**：退市常态化（2024年退市超50家），壳价值急剧缩水
- **市场风格切换**：大盘价值风格跑赢，红利低波成为市场热点
- **量化指增表现亮眼**：2025年量化指增产品平均收益率45%，近九成跑赢基准

#### 4.3.2 小市值策略现状

截至2025年中，小市值因子拥挤度约1.07（国泰君安数据），小微盘股成交额占全市场比例升至48%，接近历史峰值。中证2000指数年内涨幅16.41%，多家头部量化私募旗下产品收益率超20%。

**关键判断**：小市值策略仍有alpha，但纯小市值轮动的超额收益大幅衰减。需要叠加多因子（质量、价值、动量）增强，且必须严格控制拥挤度监控。

#### 4.3.3 散户主导市场的Alpha来源

A股散户交易占比约65%，创造了独特的行为金融alpha：
- **短期反转效应**：散户追涨杀跌导致1-4周反转策略长期有效
- **彩票偏好**：散户偏爱高波动概念股，低波因子有持续alpha
- **注意力效应**：涨停板、龙虎榜吸引跟风，形成短期动量

### 4.4 资金量对策略选择的影响

10万资金的优劣势分析：

| 维度 | 优势 | 劣势 |
|------|------|------|
| 策略容量 | 任何策略都能跑 | - |
| 交易成本 | - | 占比高（年化1-2%+） |
| 分散度 | - | 最多8-10只股票 |
| 打新 | 可参与（年化增厚1-3%） | - |
| 衍生品 | - | 不满足50万门槛 |

**推荐策略优先级**：
1. ★★★ **红利低波+小市值混合**：高股息+低波+小盘三因子，平衡收益与风险
2. ★★★ **多因子价值+质量增强**：PB+ROE双因子选股，"便宜的好公司"
3. ★★ **LLM增强因子策略**：在传统因子基础上，用DeepSeek挖掘增量因子
4. ★★ **打新+底仓策略**：ETF+蓝筹做底仓兼顾打新增厚

---

## 五、对我们系统的具体建议

### 5.1 架构建议

基于我们的条件（HP 800 G1、无GPU、10万资金、月频、A股小市值），建议以下技术架构：

```
┌─────────────────────────────────────────────┐
│              DeepSeek V4 Flash（API）          │
│    因子假设生成 / 代码生成 / 文本理解           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           RD-Agent (本地部署)                  │
│    假设→代码→回测→反馈 迭代循环               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        Qlib (本地部署, CPU模式)               │
│   因子计算 / 模型训练 / 回测引擎              │
├─────────────────────────────────────────────┤
│  数据层: 5205只A股K线+财务（已有）            │
│         + AKShare补充（行业、资金流等）       │
└─────────────────────────────────────────────┘
```

### 5.2 分阶段实施路线

**第一阶段（1-2月）：基础设施搭建**
- 在HP 800 G1上部署Qlib，注入已有5205只A股数据
- 配置RD-Agent使用DeepSeek V4 Flash作为后端LLM
- 用Qlib内置Alpha158因子库跑通月频回测管道
- 验证回测中的涨跌停、停牌、T+1处理是否正确

**第二阶段（2-4月）：基线策略建立**
- 实现小市值+红利低波混合策略作为基线
- 运行Walk-Forward分析验证基线策略稳健性
- 建立因子有效性监控体系（IC、IC_IR、换手率、衰减曲线）
- 对Qlib内置因子做全因子检验，建立因子库

**第三阶段（4-8月）：LLM因子挖掘接入**
- 配置RD-Agent的`fin_factor`循环，使用DeepSeek做因子自动发现
- 加入AlphaAgent的三个正则化机制（原创性约束、假设-因子对齐、复杂度控制）
- 将LLM挖掘的因子与传统因子做正交化处理后叠加
- 每轮迭代后人工审核因子的经济逻辑

**第四阶段（8-12月）：模拟盘验证与迭代**
- 最优策略上模拟盘3-6个月
- 监控实盘与回测的偏离度
- 根据偏离度调整滑点假设和交易成本模型
- 建立因子衰减告警机制

### 5.3 DeepSeek在因子挖掘中的具体用法

基于RD-Agent已支持DeepSeek的现状和信达证券的研究实践：

1. **因子假设生成**：让DeepSeek分析近期市场特征，生成候选因子表达式假设
2. **因子代码实现**：DeepSeek-Coder生成Qlib格式的因子计算代码
3. **研报因子提取**：用DeepSeek处理券商研报PDF，提取研报中提到的因子逻辑并编码
4. **因子解释性审核**：让DeepSeek为每个生成的因子提供经济学解释，人工审核
5. **成本控制**：因子迭代阶段用DeepSeek（低成本），最终因子筛选阶段可用更强模型

**关键注意**：截至调研时，没有发现专门以DeepSeek为核心模型的同行评审因子挖掘学术论文。DeepSeek的优势在于成本效益，在因子挖掘这种需要大量迭代的场景中是实际优势，但在金融领域特定基准测试上的系统评估仍然有限。

### 5.4 CPU本地执行的优化建议

无GPU并不意味着不能做AI量化。以下方案均可在CPU上运行：

- **LightGBM/XGBoost**：CPU原生支持，是Qlib中表现最好的基线模型
- **DeepSeek API调用**：模型在云端推理，本地只负责调度和回测
- **RD-Agent**：核心逻辑是LLM调度+代码执行，不需要本地GPU
- **vectorbt**：基于Numba JIT的向量化计算，纯CPU但速度极快
- **轻量深度学习**：如需尝试，可用ONNX Runtime的CPU优化版部署小模型

**性能优化**：
- 使用Polars替代Pandas做数据处理（Rust内核，CPU效率高）
- 因子计算并行化：Python multiprocessing或joblib
- 回测向量化：优先用vectorbt而非事件驱动框架

---

## 六、应避免的常见坑

### 6.1 因子挖掘中的坑

1. **多重检验陷阱**：LLM可以快速生成海量因子，但每多检验一个因子，发现"显著"但无效因子的概率就增加。必须使用Bonferroni校正或FDR控制。
2. **数据窥探偏差**：LLM在训练中可能已"见过"历史金融数据和已发表因子，导致生成因子看似有效实为记忆。
3. **追逐高IC**：IC>0.1的因子在实盘中几乎不可能持续，大概率是过拟合。预期训练集IC=0.08，实盘能保留0.04就很好了。
4. **忽视经济直觉**：没有合理解释的因子，即使IC高也不用——可能是数据挖掘偏差。

### 6.2 回测中的坑

5. **幸存者偏差**：只回测现存股票，忽略已退市股票。A股2024年退市超50家，影响显著。
6. **忽略涨跌停**：回测框架默认成交导致收益虚高，特别是小市值策略。
7. **低估交易成本**：小市值滑点远大于大盘股，保守按千2估计。
8. **前视偏差**：财务数据必须使用发布日期（报告期+延迟），不能用报告期日期。

### 6.3 策略选择中的坑

9. **纯小市值轮动**：2024年微盘股闪崩已证明策略脆弱性。必须叠加其他因子增强。
10. **过度依赖单一LLM**：所有团队都用类似LLM（如RD-Agent+GPT-4）会导致因子高度同质化，加速拥挤和衰减。建议多模型交叉。
11. **忽视拥挤度监控**：策略的容量和拥挤度比alpha本身更重要。设定拥挤度阈值，超标时减仓。
12. **频繁修改参数**：实盘至少运行6个月再评价策略成败，不要因为短期回撤就修改参数。

### 6.4 技术选择中的坑

13. **过早追求实盘**：研究框架（Qlib）和实盘框架（NautilusTrader）应分阶段引入，不要一开始就追求全流程实盘。
14. **忽视数据质量**：数据是根本，再好的模型也救不了垃圾数据。多源交叉验证。
15. **过度工程化**：对于10万资金+月频策略，简单的多因子模型+纪律性执行，远胜复杂的深度学习黑箱。

---

## 七、推荐学习资源和开源项目

### 7.1 核心开源项目

| 项目 | 地址 | 用途 |
|------|------|------|
| Qlib | github.com/microsoft/qlib | 量化研究全流程平台 |
| RD-Agent | github.com/microsoft/RD-Agent | LLM驱动因子自动挖掘 |
| FinRL | github.com/AI4Finance-Foundation/FinRL | 强化学习量化框架 |
| FinGPT | github.com/AI4Finance-Foundation/FinGPT | 金融大语言模型 |
| vectorbt | github.com/polakowo/vectorbt | 极速向量化回测 |
| AKShare | github.com/akfamily/akshare | 免费A股数据接口 |
| AlphaAgent | github.com/RndmVariableQ/AlphaAgent | 抗衰减因子挖掘 |

### 7.2 推荐论文阅读顺序

**入门必读**：
1. FinGPT（arXiv:2306.06031）——理解金融LLM的全貌
2. Qlib论文——理解量化研究平台设计

**核心研究**：
3. RD-Agent(Q)（arXiv:2505.15155）——LLM因子挖掘的里程碑
4. AlphaAgent（arXiv:2502.16789）——抗因子衰减机制
5. LLMFactor（ACL 2024）——从文本提取因子

**方向拓展**：
6. FinRL Contest 2025（arXiv:2504.02400）——RL量化基准
7. CN-Buzz2Portfolio（arXiv:2603.22305）——中文LLM金融评测
8. Chain-of-Alpha——双链因子挖掘

### 7.3 社区与持续学习

- **聚宽社区**：国内最活跃的量化社区，优质帖子质量高
- **Awesome-LLM-Quantitative-Trading-Papers**（GitHub）：LLM量化论文持续更新合集
- **arXiv q-fin.CP和q-fin.TR分类**：金融量化最新论文
- **微软RD-Agent Discord/微信群**：RD-Agent官方社区
- **FinRL Discord**：金融RL社区

### 7.4 推荐技术栈组合

针对我们的条件，推荐以下技术栈：

```
数据层：已有5205只A股数据 + AKShare补充
计算层：Qlib（因子计算+回测）+ Polars（数据处理）
AI层：  RD-Agent + DeepSeek V4 Flash（因子挖掘）
验证层：vectorbt（快速参数优化）+ 自建Walk-Forward
监控层：自建因子衰减监控 + 拥挤度跟踪
```

---

## 八、参考文献

### LLM因子挖掘
1. Xu Yang, Xiao Yang et al. "R&D-Agent-Quant: A Multi-Agent Framework for Data-Centric Factors and Model Joint Optimization." NeurIPS 2025. arXiv:2505.15155.
2. Ziyi Tang et al. "AlphaAgent: LLM-Driven Alpha Mining with Regularized Exploration to Counteract Alpha Decay." arXiv:2502.16789, 2025.
3. "Chain-of-Alpha: Unleashing the Power of Large Language Models for Alpha Mining in Quantitative Trading." 2025.
4. Meiyun Wang, Kiyoshi Izumi, Hiroki Sakaji. "LLMFactor: Extracting Profitable Factors through Prompts." ACL 2024 Findings.
5. "FactorMAD: A Multi-Agent Debate Framework Based on Large Language Models." ACM, doi:10.1145/3768292.3770377.
6. Liyuan Chen et al. "CN-Buzz2Portfolio: A Chinese-Market Dataset and Benchmark for LLM-Based Macro and Sector Asset Allocation." arXiv:2603.22305, 2026.
7. Hongyang Yang et al. "FinGPT: Open-Source Financial Large Language Models." arXiv:2306.06031, FinLLM@IJCAI 2023.
8. "Automate Strategy Finding with LLM in Quant Investment." arXiv:2409.06289.
9. "LLMs for Quantitative Investment Research: A Practitioner's Guide." SSRN 5934015.
10. 信达金工."深度学习揭秘系列之三：用DeepSeek优化价量因子." 2025年3月.

### 金融LLM
11. Shijie Wu et al. "BloombergGPT: A Large Language Model for Finance." arXiv:2303.17564, 2023.
12. "FinRobot: An Open-Source AI Agent Platform for Financial Applications." arXiv:2405.14767, 2024.
13. Xu Yang et al. "An LLM-Agent Framework Towards Autonomous Data Science." arXiv:2505.14738, 2025.

### 强化学习
14. Keyi Wang et al. "FinRL Contests: Benchmarking Data-driven Financial RL Agents." arXiv:2504.02400, 2025.
15. Boris Belyakov. "AlphaZeroBeta: Deep RL for Market-Neutral Portfolios." 2026.
16. Igor Halperin, Andrey Itkin. "SciPhy RL for Portfolio Optimization." 2026.
17. Eun Go et al. "Plan Before You Trade: FPILOT." 2026.

### 图神经网络
18. Amber Li et al. "Structure Over Signal: Multi-relational GNNs for Stock Prediction." 2025.
19. Yonggai Zhuang et al. "GRU-PFG: Extract Inter-Stock Correlation from Stock Factors with GNN." 2024.
20. Yingjie Niu et al. "Evaluating Financial Relational Graphs: Interpretation Before Prediction." 2024.

### A股与最佳实践
21. 国泰君安证券."量化择时和拥挤度预警周报." 2025年7月.
22. 展恒基金."小微盘量化拥挤度再审视." 2025.
23. 东方财富."平均收益率超45%！2025量化指增策略全景解读." 2026年1月.
24. 新浪财经."中小市值策略持续火热！百亿量化业绩炸裂." 2025年7月.

---

> **免责声明**：本报告为研究调研整理，不构成投资建议。量化投资有风险，回测不代表未来收益。参考文献中的观点归原作者所有，引用不等于 endorsement。

> **报告路径**: `shared/results/02-AI技术调研/R-190-量化投资AI-Agent最新研究与最佳实践.md`  
> **素材文件**: `shared/results/work/r190-01` 至 `r190-04`
