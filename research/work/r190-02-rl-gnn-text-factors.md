# 强化学习组合优化、图神经网络选股、文本因子最新进展

> 调研时间：2026年8月  
> 覆盖范围：2024-2026年重要论文、开源项目及实际应用评估

---

## 一、强化学习在组合优化中的应用（2024-2026）

### 1.1 总体趋势

强化学习（RL）在组合优化中的应用正从学术探索走向实际部署。2024年以来，研究焦点已经从简单的"RL能否超越均值-方差"转向更加务实的方向：**动态仓位调整、风险控制、交易执行优化、市场状态切换**等。深度强化学习（DRL）框架（如PPO、SAC、DDPG）已成为量化金融RL研究的标配算法族。

### 1.2 重大论文与研究成果

#### （1）AlphaZeroBeta: Deep Reinforcement Learning for Market-Neutral Portfolios
- **作者**: Boris Belyakov
- **发表时间**: 2026年7月，arXiv
- **核心内容**: 将AlphaZero式的自博弈思想引入市场中性组合构建。传统方法依赖因子模型或凸优化，该论文用深度RL直接学习alpha因子权重，同时控制系统性风险暴露。
- **实用性评价**: 概念创新，但市场中性约束下的RL训练稳定性仍是难题。适合作为多策略体系中的补充模块，而非独立策略。

#### （2）SciPhy Reinforcement Learning for Portfolio Optimization
- **作者**: Igor Halperin, Andrey Itkin
- **发表时间**: 2026年7月，arXiv
- **核心内容**: 提出了一种基于物理启发的动态组合优化框架，将RL与随机控制理论结合，用"科学计算+物理模型"的方式指导RL策略学习。
- **实用性评价**: Igor Halperin是量化金融AI领域的资深研究者，其方法强调可解释性和理论一致性，对于大型机构投资者具有参考价值。

#### （3）Reinforcement Learning for Risk-Sensitive Investment Management: a Free Energy–Entropy Duality Approach
- **作者**: Sebastien Léo, Wolfgang Runggaldier
- **发表时间**: 2026年6月，arXiv
- **核心内容**: 将风险敏感型资产配置问题转化为连续时间RL问题，利用自由能-熵对偶性解决部分模型未知情况下的最优策略学习。
- **实用性评价**: 理论扎实，风险敏感框架更接近实际投资需求，但实现复杂度较高。

#### （4）Deep Reinforcement Learning Framework for Diversified Portfolio Management Across Global Equity Markets
- **作者**: Kamil Kashif, Robert Ślepaczuk
- **发表时间**: 2026年5月，arXiv
- **核心内容**: 开发并评估了一个DRL框架，用于全球股票市场的分散化组合管理。研究跨越多个市场（包括发达市场和新兴市场），评估了不同RL算法（PPO、A2C、DDPG）在夏普比率和最大回撤等指标上的表现。
- **实用性评价**: 较为系统性的实证研究，对实际部署有直接参考价值。但需要注意过拟合风险，全球市场配置涉及汇率和政治风险，RL模型未必能充分捕捉。

#### （5）Plan Before You Trade: Inference-Time Optimization for RL Trading Agents (FPILOT)
- **作者**: Eun Go, Rohan Deb, Arindam Banerjee
- **发表时间**: 2026年5月，arXiv
- **核心内容**: 提出FPILOT框架，在推理阶段利用价格预测优化RL交易代理的决策。传统RL代理以静态策略部署，该论文在推理时增加优化环节，显著提升了性能。
- **实用性评价**: 创新性强，推理时优化是一个重要方向。实际部署中可考虑结合实时预测模型，增强RL策略的适应性。

#### （6）EvoNash-MARL: A Closed-Loop Multi-Agent Reinforcement Learning Framework for Medium-Horizon Equity Allocation
- **作者**: Chongliu Jia, Yi Luo, Sipeng Han 等
- **发表时间**: 2026年4月，arXiv
- **核心内容**: 针对中期股票配置，提出多智能体RL框架。利用演化博弈论中的纳什均衡概念，解决多策略智能体在分布偏移下的鲁棒性问题。
- **实用性评价**: 多智能体框架适合模拟多策略组合管理场景，但训练和推理成本较高。

#### （7）Addressing Market Regime Changes and Heavy-Tailed Returns via Bayesian VAR and Elliptical Black-Litterman
- **作者**: Daniil Mikriukov, Ruoyu Sun 等
- **发表时间**: 2026年6月，arXiv
- **核心内容**: 指出DRL组合优化框架在市场状态切换和厚尾收益下的不足，提出结合贝叶斯VAR和椭圆Black-Litterman模型来增强鲁棒性。
- **实用性评价**: 直接解决了RL在金融中最大的痛点——非平稳分布下的策略退化问题。

#### （8）A Meta Reinforcement Learning Approach to Goals-Based Wealth Management
- **作者**: Sanjiv R. Das, Harshad Khadilkar
- **发表时间**: 2026年5月，arXiv
- **核心内容**: 将元学习引入目标导向的财富管理，用RL代理学习如何在不同的投资目标（退休、教育基金等）间快速适应。
- **实用性评价**: 财富管理和智能投顾领域的创新，实用性较好。

### 1.3 FinRL框架最新进展

FinRL（https://github.com/AI4Finance-Foundation/FinRL）是AI4Finance Foundation维护的开源项目，是目前最活跃的金融RL框架。

**核心论文系列**:
- **FinRL: A Deep Reinforcement Learning Library for Automated Stock Trading** (Xiao-Yang Liu, Hongyang Yang 等, 2020, arXiv:2011.09607) — 初版框架论文
- **FinRL-Meta: Market Environments and Benchmarks for Data-Driven Financial RL** (Xiao-Yang Liu, Ziyi Xia 等, 2022, arXiv:2211.03107) — 市场环境数据引擎
- **FinRL-Podracer: High Performance and Scalable DRL for Quantitative Finance** (Zechu Li, Xiao-Yang Liu 等, 2021) — 高性能并行训练
- **FinRL Contests: Benchmarking Data-driven Financial Reinforcement Learning Agents** (Keyi Wang, Nikolaus Holzer 等, 2025年4月, arXiv:2504.02400) — 竞赛基准评测

**2024-2025年重要更新**:
- **Multi-Objective Bayesian Optimization of DRL for ESG Financial Portfolio Management** (2025年12月, arXiv) — 将FinRL用于ESG组合管理，结合贝叶斯优化进行多目标搜索
- **Deep Reinforcement Learning for ESG Financial Portfolio Management** (Garrido-Merchán 等, 2023) — FinRL在ESG投资中的系统应用

**FinRL框架特点**:
- 模块化设计：数据获取 → 环境构建 → RL代理训练 → 回测评估
- 支持多种RL算法：PPO, SAC, DDPG, A2C, TD3
- 内置美股、A股、加密货币等多种市场环境
- 活跃的社区维护，Star数超过10k

**实际应用挑战**:
1. **过拟合风险**: 金融数据信噪比极低，RL容易在训练集上过拟合
2. **非平稳性**: 市场分布不断变化，训练好的策略可能快速失效
3. **交易成本建模**: 现实中的滑点、冲击成本、手续费需要精确建模
4. **可解释性差**: 深度RL策略通常是黑箱，难以满足合规要求
5. **样本效率低**: RL需要大量交互数据，而金融数据有限

### 1.4 RL在交易执行优化中的应用

交易执行是RL在金融中最接近实际应用的领域。

**关键论文**:
- **Optimal Execution with Reinforcement Learning** (2024年11月提交, 2025年11月更新, arXiv) — 研究RL在最优执行中的应用，解决大单拆分问题
- **Reinforcement Learning in Queue-Reactive Models: Application to Optimal Execution** (Tomas España, Yadh Hafsi, Fabrizio Lillo, Edoardo Vittori, 2025年11月, arXiv) — 在队列反应模型中使用RL优化执行策略
- **Reinforcement Learning in Non-Markov Market-Making** (Luca Lalor, Anatoliy Swishchuk, 2024年10月, arXiv) — 在非马尔可夫做市场景中使用深度RL
- **MOT: A Mixture of Actors RL Method by Optimal Transport for Algorithmic Trading** (2024, arXiv) — 利用最优传输理论的多演员RL算法用于算法交易

**实用性评价**: 交易执行是RL最适合的金融场景，因为：
- 目标明确（最小化执行成本/VWAP跟踪误差）
- 环境可模拟（订单簿数据）
- 反馈迅速（日内可多次评估）
- 已有券商和对冲基金在实际部署RL执行算法

---

## 二、图神经网络（GNN）选股

### 2.1 总体趋势

GNN在选股中的核心思想是：**股票不是孤立的，它们之间存在丰富的关联关系**（供应链关系、行业归属、共同因子暴露、资金流向等）。GNN能够自然地建模这些关系结构，从而捕捉传统因子模型遗漏的交互信息。

2024-2025年的研究趋势：
- 从简单的股票关联图→多关系异构图
- 从静态图结构→动态时变图
- 从纯GNN→GNN+Transformer、GNN+Mamba等混合架构
- 更加强调可解释性和图结构的金融含义

### 2.2 重要论文与研究成果

#### （1）Gated Fusion Enhanced Multi-Scale Hierarchical GCN for Stock Movement Prediction
- **作者**: Xiaosha Xue, Peibo Duan, Zhipeng Liu, Qi Chu, Changsheng Zhang, Bin Zhang
- **发表时间**: 2025年11月，arXiv
- **核心内容**: 提出多尺度层次化图卷积网络（GCN），结合门控融合机制，在不同时间尺度上捕捉股票间的关联模式。
- **实用性评价**: 多尺度设计符合金融数据的特征（短期动量+长期均值回归），但工程复杂度较高。

#### （2）Structure Over Signal: A Globalized Approach to Multi-relational GNNs for Stock Prediction
- **作者**: Amber Li, Aruzhan Abil, Juno Marques Oda
- **发表时间**: 2025年10月，arXiv
- **核心内容**: 强调**结构优于信号**的理念，提出多关系GNN的全局化方法。论文指出，不同类型的股票关系（行业、供应链、因子暴露）应建模为异构多关系图。
- **实用性评价**: 思路正确——金融市场中关系类型多样，单一关系图不足以捕捉全部信息。

#### （3）EP-GAT: Energy-based Parallel Graph Attention Neural Network for Stock Trend Classification
- **作者**: Zhuodong Jiang, Pengju Zhang, Peter Martin
- **发表时间**: 2025年7月（v1），2026年3月更新，arXiv
- **核心内容**: 提出基于能量的并行图注意力网络，用于股票趋势分类。图注意力机制（GAT）可以自适应学习不同股票间的重要性权重。
- **实用性评价**: GAT在股票关联建模中比GCN更灵活，能量函数增加了可解释性。

#### （4）Mamba Meets Financial Markets: A Graph-Mamba Approach for Stock Price Prediction
- **作者**: Ali Mehrabian, Ehsan Hoseinzade, Mahdi Mazloum, Xiao...
- **发表时间**: 2024-2025年，arXiv
- **核心内容**: 将2024年最热门的Mamba架构（状态空间模型）与图结构结合，用于股价预测。Mamba解决了Transformer在长序列建模中的计算效率问题。
- **实用性评价**: Mamba+GNN的组合在效率上有优势，但金融时间序列的有效长度通常不长，Mamba的优势可能不如在NLP领域明显。

#### （5）A Distillation-based Future-aware GNN for Stock Trend Prediction
- **作者**: Zhipeng Liu, Peibo Duan, Mingyang Geng, Bin Zhang
- **发表时间**: 2025年2月，arXiv
- **核心内容**: 利用知识蒸馏技术，将未来信息融入GNN的预测中，同时避免信息泄露。
- **实用性评价**: 知识蒸馏技巧巧妙，但需谨慎处理前视偏差。

#### （6）Stock Price Prediction Using a Hybrid LSTM-GNN Model
- **作者**: Meet Sonani, Atta Badii, Armin Moin
- **发表时间**: 2025年2月，arXiv
- **核心内容**: 结合LSTM（捕捉时序特征）和GNN（捕捉股票关联）的混合模型。
- **实用性评价**: LSTM+GNN是最经典的时序+图结构组合方案，工程实现简单，适合作为baseline。

#### （7）GRU-PFG: Extract Inter-Stock Correlation from Stock Factors with GNN
- **作者**: Yonggai Zhuang, Haoran Chen, Kequan Wang, Teng Fei
- **发表时间**: 2024年11月，arXiv
- **核心内容**: 从传统因子（如Barra因子）中提取股票间关联，用GNN增强因子选股效果。
- **实用性评价**: 将传统量化因子与GNN结合的务实思路，适合已有因子框架的团队在现有基础上增量改进。

#### （8）Evaluating Financial Relational Graphs: Interpretation Before Prediction
- **作者**: Yingjie Niu, Lanxin Lu, Rian Dolphin, Valerio Poti, Ruihai Dong
- **发表时间**: 2024年9月-10月，arXiv
- **核心内容**: 系统评估不同金融关系图（行业分类图、供应链图、因子相关图等）对预测性能的影响，**强调先理解图结构含义再做预测**。
- **实用性评价**: 极具参考价值的综述性工作。给实践者的启示是：不是所有"图"都能带来alpha，图结构的金融逻辑比GNN架构本身更重要。

#### （9）Stock Type Prediction Model Based on Hierarchical GNN
- **作者**: Jianhua Yao, Yuxin Dong, Jiajing Wang 等
- **发表时间**: 2024年12月，arXiv
- **核心内容**: 提出层次化GNN进行股票类型预测，通过分层聚合不同粒度的信息（个股→行业→板块）。
- **实用性评价**: 层次化建模符合A股市场的行业板块结构。

#### （10）Forecasting Equity Correlations with Hybrid Transformer-GNN
- **发表时间**: 2026年1月，arXiv
- **核心内容**: 用Transformer处理时序特征，GNN捕捉截面关联，预测股票相关性矩阵的前瞻变化。
- **实用性评价**: 预测相关性矩阵比直接预测收益更稳定，可用于风险预算和多因子组合构建。

#### （11）Unleashing Expert Opinion from Social Media for Stock Prediction
- **作者**: Wanyun Zhou, Saizhuo Wang, Xiang Li, Yiyan Qi, Jian Guo, Xiaowen Chu
- **发表时间**: 2025年4月（v1），2025年11月更新，arXiv
- **核心内容**: 从社交媒体中提取专家观点，结合GNN进行选股。
- **实用性评价**: 将NLP与GNN结合的尝试，但社交媒体数据的噪声和操纵风险需谨慎处理。

### 2.3 基于知识图谱的选股策略

金融知识图谱（Financial Knowledge Graph, FKG）是GNN选股的重要基础设施。典型的金融知识图谱包含：

- **公司实体**：上市公司、供应商、客户、竞争对手
- **关系类型**：供应链关系、股权关系、高管关系、行业归属、地域关系
- **事件节点**：并购、上市、退市、财报发布、政策变化

**重要项目**:
- **Price graphs: Utilizing the structural information of financial time series for stock prediction** (Junran Wu, Ke Xu 等, 2021, arXiv:2106.02522)  
  GitHub: https://github.com/BUAA-WJR/PriceGraph  
  将价格时间序列转化为图结构，用GNN捕捉结构性信息

**实用建议**:
1. A股的产业链数据可从Wind、同花顺iFinD等获取
2. 开源金融知识图谱项目（如OpenKG）可作为起点
3. 图的构建质量比GNN模型架构更重要——"垃圾进，垃圾出"
4. 动态图更新（如每季度更新产业链关系）是实际部署的关键

---

## 三、另类数据+LLM生成文本因子

### 3.1 总体趋势

大语言模型（LLM）正在变革金融NLP。2024-2025年的趋势：
- 从传统情感分析（正面/负面/中性）→ **多维度因子提取**（事件类型、影响程度、时间衰减、行业扩散）
- 从英文市场为主 → **中文金融文本处理**需求爆发
- 从单一新闻源 → **多源融合**（新闻+研报+社交媒体+公告）
- FinGPT等金融领域大模型的开源推动了应用落地

### 3.2 重要论文与研究成果

#### （1）LLMFactor: Extracting Profitable Factors through Prompts for Explainable Stock Movement Prediction
- **作者**: Meiyun Wang, Kiyoshi Izumi, Hiroki Sakaji
- **发表时间**: 2024年6月，ACL 2024 Findings, arXiv
- **核心内容**: 提出**LLMFactor框架**，利用顺序知识引导提示（Sequential Knowledge-Guided Prompting, SKGP）从金融新闻中提取可解释的因子。不同于简单的情感分析，LLMFactor能识别具体的驱动因素（如"新产品发布"、"管理层变动"），并将其转化为可量化的alpha信号。
- **实用性评价**: ⭐⭐⭐⭐⭐ ACL Findings论文，学术影响力大。因子提取范式比传统情感分析更深入，但需要精心设计prompt模板，且LLM推理成本较高。

#### （2）CN-Buzz2Portfolio: A Chinese-Market Dataset and Benchmark for LLM-Based Macro and Sector Asset Allocation from Daily Trending Financial News
- **作者**: Liyuan Chen, Shilong Li, Jiangpeng Yan, Shuoling Liu, Qiang Yang, Xiu Li
- **发表时间**: 2026年3月，arXiv:2603.22305
- **核心内容**: **专门针对中国市场**的LLM金融基准数据集。将每日热点新闻映射到宏观和行业资产配置（ETF层面），覆盖2024年至2025年中期。提出三阶段CPA代理工作流（Compression-Perception-Allocation），评测了9个主流LLM在中文金融决策中的表现。
- **实用性评价**: ⭐⭐⭐⭐⭐ 目前最系统的中文LLM金融评测基准。对实践者的重要启示：
  - 不同LLM在中文金融理解上差异巨大
  - ETF层面的配置比个股选择更适合LLM能力范围
  - 热点新闻→配置逻辑的映射需要多步推理

#### （3）FinGPT: Democratizing Internet-scale Data for Financial Large Language Models
- **作者**: Xiao-Yang Liu, Guoxuan Wang, Hongyang Yang, Daochen Zha
- **发表时间**: 2023年7月（v1），2023年11月更新，arXiv
- **核心内容**: FinGPT项目的核心论文，提出 democratizing 金融大模型数据。  
  GitHub: https://github.com/AI4Finance-Foundation/FinGPT
- **后续系列论文**:
  - **FinGPT: Instruction Tuning Benchmark for Open-Source LLMs in Financial Datasets** (Neng Wang, Hongyang Yang, Christina Dan Wang, 2023年10月)
  - **Instruct-FinGPT: Financial Sentiment Analysis by Instruction Tuning** (Boyu Zhang, Hongyang Yang, Xiao-Yang Liu, 2023)
  - **FinGPT-HPC: Efficient Pretraining and Finetuning LLMs for Financial Applications with HPC** (Xiao-Yang Liu 等, 2024年2月) — 高性能计算预训练
  - **Customized FinGPT Search Agents Using Foundation Models** (Felix Tian 等, 2024年10月)

**实用性评价**: FinGPT是目前最成熟的开源金融大模型生态。其价值在于：
- 提供了完整的金融数据采集→预处理→微调→部署流程
- 支持LoRA等参数高效微调方法
- 社区活跃，持续更新

#### （4）Golden Touchstone: A Comprehensive Bilingual Benchmark for Evaluating Financial LLMs
- **作者**: Xiaojun Wu, Junxi Liu, Huanyi Su 等（包括Saizhuo Wang, Jian Guo）
- **发表时间**: 2024年11月（v1），2025年12月更新，arXiv
- **核心内容**: 双语（中英文）金融LLM评测基准，全面评估了主流金融大模型在多种任务上的表现。
- **实用性评价**: 选择中文金融LLM时的重要参考。

#### （5）Evaluation and Benchmarking Suite for Financial LLMs and Agents
- **作者**: Shengyuan Lin, Kaiwen He, Jaisal Patel 等（包括Keyi Wang, Xiao-Yang Liu）
- **发表时间**: 2026年2月，arXiv
- **核心内容**: 为金融LLM和代理提供系统性的评估和基准测试套件。

#### （6）Adversarial News and Lost Profits: Manipulating Headlines in LLM-Driven Algorithmic Trading
- **作者**: Advije Rizvani, Giovanni Apruzzese, Pavel Laskov
- **发表时间**: 2026年1月，arXiv
- **核心内容**: **揭示了LLM驱动交易的安全风险**——通过篡改新闻标题可以操纵LLM交易系统的决策，导致错误交易。
- **实用性评价**: ⚠️ 重要安全警示。实际部署LLM文本因子时，必须考虑：
  - 新闻源的可靠性和防篡改
  - 对抗性文本的检测
  - 多源交叉验证

#### （7）An End-to-End LLM Enhanced Trading System
- **作者**: Ziyao Zhou, Ronitt Mehra
- **发表时间**: 2025年2月，arXiv
- **核心内容**: 构建端到端的LLM增强交易系统，从数据处理到信号生成到交易执行全链路。

#### （8）Learning Explainable Stock Predictions with Tweets Using Mixture of Experts
- **作者**: Wenyan Xu, Dawei Xiang, Rundong Wang 等
- **发表时间**: 2025年7月，arXiv
- **核心内容**: 利用Twitter（推文）数据进行可解释的股票预测，采用混合专家（MoE）架构。

#### （9）Multimodal Financial Foundation Models (MFFMs)
- **作者**: Xiao-Yang Liu, Yupeng Cao, Li Deng
- **发表时间**: 2025年5-7月，arXiv
- **核心内容**: 提出多模态金融基础模型的概念框架，整合文本、数值、图表等多种金融数据模态。

### 3.3 中文金融文本处理的特点与挑战

**特点**:
1. **语言特性**：中文金融文本涉及大量专业术语（如"北向资金"、"打新"、"融资融券"），通用LLM理解不足
2. **信息密度高**：中文研报通常信息密度远高于英文，一段话可能包含多个信号
3. **隐式情感**：中文金融写作倾向含蓄表达，"有待观察"通常偏负面，通用情感词典难以识别
4. **政策敏感**：A股高度受政策影响，政策文本（如政府工作报告、央行公告）的解读至关重要
5. **多方言表述**：不同信源（官方媒体、自媒体、股吧）的语言风格差异巨大

**挑战**:
1. **数据获取**：中文金融数据源（Wind、同花顺、东方财富）大多付费，开源数据有限
2. **标注困难**：中文金融文本的高质量标注需要领域专家，成本高昂
3. **模型选择**：通用LLM（GPT-4、Claude）中文金融理解不如英文；中文LLM（通义千问、文心一言、ChatGLM）金融能力参差不齐
4. **合规限制**：使用LLM处理研报内容可能涉及版权和合规问题
5. **时效性**：LLM的知识有截止日期，无法捕捉最新金融概念和事件

### 3.4 实际效果评估

基于现有文献和行业实践的综合评估：

| 文本因子类型 | 信息来源 | Alpha衰减速度 | 容量限制 | 实用性评级 |
|---|---|---|---|---|
| 新闻情感因子 | 财经新闻 | 快（分钟级） | 中 | ⭐⭐⭐⭐ |
| 研报情感因子 | 券商研报 | 中（日级） | 大 | ⭐⭐⭐⭐⭐ |
| 社交媒体因子 | 股吧、微博、雪球 | 极快（秒级） | 小 | ⭐⭐⭐ |
| 公告事件因子 | 交易所公告 | 慢（日级） | 大 | ⭐⭐⭐⭐⭐ |
| 政策文本因子 | 政府/监管文件 | 中（周级） | 大 | ⭐⭐⭐⭐ |

**关键发现**:
- LLM生成的文本因子在**回测中表现优异**，但实盘效果通常有显著衰减
- 研报和公告类文本因子的alpha最稳定，社交媒体因子噪声大但短期信号强
- 文本因子最有效的用法是与传统量价因子**正交化后叠加使用**，而非独立使用
- LLM的推理成本是需要实际考虑的部署因素（处理全市场新闻需GPU集群）

---

## 四、开源项目汇总

| 项目名称 | GitHub | 领域 | 说明 |
|---|---|---|---|
| FinRL | https://github.com/AI4Finance-Foundation/FinRL | RL组合优化 | 最活跃的金融RL框架 |
| FinGPT | https://github.com/AI4Finance-Foundation/FinGPT | 金融LLM | 开源金融大模型生态 |
| FinRL-Meta | FinRL子项目 | RL数据环境 | 市场数据和基准环境 |
| PriceGraph | https://github.com/BUAA-WJR/PriceGraph | GNN选股 | 价格图结构选股模型 |
| qlib | https://github.com/microsoft/qlib | 量化平台 | 微软开源AI量化平台，支持GNN |
| StockMovementPrediction | https://github.com/fulifeng/Temporal_Relational_Stock_Ranking | GNN选股 | 时序关系图选股经典项目 |

> **注**: qlib（微软亚洲研究院）虽然不是专门的GNN/RL项目，但提供了完整的数据管理、因子计算、模型训练和回测框架，可作为上述技术的工程基座。

---

## 五、总结与实践建议

### 5.1 技术成熟度评估

| 技术方向 | 学术成熟度 | 工程落地难度 | 实际部署案例 | 推荐策略 |
|---|---|---|---|---|
| RL组合优化 | ⭐⭐⭐⭐ | 高 | 少量对冲基金 | 适合中大型团队探索 |
| RL交易执行 | ⭐⭐⭐⭐⭐ | 中 | 多家券商/对冲基金 | **最推荐优先落地** |
| GNN选股 | ⭐⭐⭐⭐ | 中 | 少量量化私募 | 适合增量改进现有因子体系 |
| LLM文本因子 | ⭐⭐⭐ | 中-高 | 快速增长 | **高潜力，建议重点投入** |
| FinGPT金融LLM | ⭐⭐⭐ | 中 | 社区活跃 | 适合作为基础设施 |

### 5.2 实践建议

1. **RL方向**: 从交易执行场景入手（如VWAP/IS策略增强），风险可控、反馈快速。组合层面RL更适合作为辅助决策工具而非全自动交易系统。

2. **GNN方向**: 先构建高质量金融关系图（行业分类+供应链+因子相关），再考虑复杂GNN架构。"Evaluating Financial Relational Graphs"论文的核心启示——图结构的金融含义比模型架构更重要。

3. **LLM文本因子方向**:
   - 从研报和公告文本入手，信号质量最高
   - 使用LLM进行事件提取+情感分析，而非简单的正负面分类
   - 参考LLMFactor的SKGP方法，将因子提取过程结构化
   - 文本因子与传统因子正交化后使用效果最佳
   - 对A股市场，关注CN-Buzz2Portfolio的评测结论

4. **工程建议**:
   - 基于qlib或FinRL搭建统一基础设施
   - 文本因子处理流水线：数据采集→LLM推理→因子计算→回测验证→实盘部署
   - 关注LLM推理成本优化（量化、蒸馏、缓存）
   - 建立文本因子的衰减监控和定期更新机制

---

## 参考文献索引

### 强化学习
1. Belyakov, B. (2026). AlphaZeroBeta: Deep RL for Market-Neutral Portfolios. arXiv.
2. Halperin, I., Itkin, A. (2026). SciPhy RL for Portfolio Optimization. arXiv.
3. Léo, S., Runggaldier, W. (2026). RL for Risk-Sensitive Investment Management. arXiv.
4. Kashif, K., Ślepaczuk, R. (2026). DRL Framework for Diversified Portfolio Management. arXiv.
5. Go, E., Deb, R., Banerjee, A. (2026). Plan Before You Trade: FPILOT. arXiv.
6. Jia, C. et al. (2026). EvoNash-MARL for Medium-Horizon Equity Allocation. arXiv.
7. Wang, K. et al. (2025). FinRL Contests: Benchmarking Financial RL Agents. arXiv:2504.02400.
8. España, T. et al. (2025). RL in Queue-Reactive Models: Optimal Execution. arXiv.
9. Lalor, L., Swishchuk, A. (2024). RL in Non-Markov Market-Making. arXiv.
10. Das, S. R., Khadilkar, H. (2026). A Meta RL Approach to Goals-Based Wealth Management. arXiv.

### 图神经网络
11. Xue, X. et al. (2025). Gated Fusion Enhanced Multi-Scale Hierarchical GCN. arXiv.
12. Li, A., Abil, A., Oda, J. M. (2025). Structure Over Signal: Multi-relational GNNs. arXiv.
13. Jiang, Z., Zhang, P., Martin, P. (2025). EP-GAT: Energy-based Parallel GAT. arXiv.
14. Mehrabian, A. et al. (2024). Graph-Mamba for Stock Price Prediction. arXiv.
15. Liu, Z. et al. (2025). Distillation-based Future-aware GNN. arXiv.
16. Zhuang, Y. et al. (2024). GRU-PFG: GNN from Stock Factors. arXiv.
17. Niu, Y. et al. (2024). Evaluating Financial Relational Graphs. arXiv.
18. Wu, J. et al. (2021). Price graphs for stock prediction. arXiv:2106.02522.
19. Yao, J. et al. (2024). Stock Type Prediction with Hierarchical GNN. arXiv.
20. Sonani, M. et al. (2025). Hybrid LSTM-GNN Model. arXiv.
21. Zhou, W. et al. (2025). Unleashing Expert Opinion from Social Media. arXiv.

### LLM与文本因子
22. Wang, M., Izumi, K., Sakaji, H. (2024). LLMFactor: Extracting Profitable Factors through Prompts. ACL 2024 Findings.
23. Chen, L. et al. (2026). CN-Buzz2Portfolio: Chinese-Market LLM Benchmark. arXiv:2603.22305.
24. Liu, X. et al. (2023). FinGPT: Democratizing Internet-scale Data. arXiv.
25. Wu, X. et al. (2024). Golden Touchstone: Bilingual Financial LLM Benchmark. arXiv.
26. Rizvani, A., Apruzzese, G., Laskov, P. (2026). Adversarial News in LLM-Driven Trading. arXiv.
27. Liu, X., Cao, Y., Deng, L. (2025). Multimodal Financial Foundation Models. arXiv.
28. Lin, S. et al. (2026). Evaluation and Benchmarking Suite for Financial LLMs. arXiv.
29. Zhou, Z., Mehra, R. (2025). End-to-End LLM Enhanced Trading System. arXiv.
30. Xu, W. et al. (2025). Explainable Stock Predictions with Tweets via MoE. arXiv.