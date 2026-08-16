# 调研底稿：回测方法论 / 平台架构 / 回退机制

## 过拟合防范（López de Prado 体系）
- Deflated Sharpe Ratio (DSR)：校正多重检验选择偏倚与非正态性。论文 "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality" (Bailey & López de Prado, SSRN 2460551)。核心思想：回测 Sharpe 是从 N 次试验中挑出的最大值时，需按试验次数、收益偏度/峰度折减后再判断显著性。
- Probability of Backtest Overfitting (PBO)：The probability of backtest overfitting (Bailey et al., Journal of Computational Finance 2017)
- Combinatorial Purged Cross-Validation (CPCV)：Advances in Financial Machine Learning (Wiley 2018) 第12章；用于替代单一 train/test 划分，生成多条 OOS 路径
- Purged K-Fold + Embargo：训练/验证集时间重叠样本需清除，避免数据泄漏
- 2024 综述：Backtest overfitting in the machine learning era (Knowledge-Based Systems, ScienceDirect S0950705124011110)

## LEAN 引擎（QuantConnect）
- 开源引擎，同一 API 贯穿 research → backtest → optimization → live trading；"unified API for research, backtesting, and live trading"
- https://github.com/quantconnect/lean ; https://www.quantconnect.com/docs/v2/lean-engine/getting-started
- 特点：事件驱动架构、多市场、结果统一存档；本地 LEAN 可免费回测+实盘，云端提供数据/算力/调度

## 回退与灰度机制（ML/DevOps 标准映射到策略部署）
- Blue-Green：双环境并行，旧版本保留，可瞬时切回
- Canary：新版本先接 1%-10% 流量（对应策略：新模型先跑 5%-10% 资金或仅 paper），观察期通过后逐步放量
- Shadow（影子）：新版本接收生产流量但不真实下单——与我们"影子并行"一致，属 ML 标准做法
- 来源：Harness blog (blue-green-canary-deployment-strategies)、bugfree.ai ML canary 指南、datarekha.com MLOps deployment strategies

## 米筐/聚宽 模拟盘→实盘惯例
- Ricequant：回测→实时模拟（Level-1 实时行情驱动）→实盘（RQAlphaPlus 框架直接复用），模拟与实盘同引擎
- JoinQuant：需先回测通过才能创建模拟交易；模拟交易可替换代码但仅限对应回测详情；实盘需外接 QMT 等
- 国内个人实盘路径普遍是"平台模拟盘 + QMT/PTrade 券商终端"组合

## vnpy 风控
- 事前风控模块（RiskManager）：单笔委托量/下单流量/持仓上限/委托价格偏离等，防错误算法逻辑下连环下单
- 架构：事件驱动引擎 + 独立 App 生态（CTA/算法交易/数据管理/风控）
- https://www.vnpy.com/docs/cn/community/info/introduction.html
