# R-204 主笔记：国际平台 / 回测验证 / 自动化进化 / 决策留痕（research-lead 自查部分）

## 1. QuantConnect LEAN（国际标杆，云+开源双形态）
来源：
- https://www.quantconnect.com/ （统一API：research → backtest → live）
- https://www.lean.io/ （LEAN 开源引擎：Research, Backtest, Optimize, Live-trade）
- https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading
- https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading

要点：
- 核心理念：**同一套算法代码、同一引擎（LEAN）跨 research/backtest/paper/live 四态运行**，只切换数据源与经纪商实现。回测与实盘的一致性由架构保证，而非由人保证。
- Paper Trading 是"一等公民 brokerage"：部署流程与真实券商（IB/Alpaca/Schwab 等 20+）完全同构，`lean cloud live deploy --push` 一条命令上线，切换 paper→live 只改 brokerage 配置。
- 上线部署清单（wizard 内置）：通知配置（email/webhook/SMS/Telegram 订单事件）、**自动重启（runtime error 后自动恢复）**、初始资金与持仓设定（可继承上一次持仓，保证连续性）、live 节点选择、实时数据源选择。
- `lean cloud status` 可查 Live status / Live id / Brokerage / Launched 时间——实盘运行有唯一 ID 与状态机。
- 研究端：Jupyter notebook 研究环境 + 高性能回测器（LEAN）+ 优化器 + 实盘，代码优先（code-first）。

## 2. Microsoft Qlib（AI 量化平台标杆，RD-Agent 母体）
来源：
- https://github.com/microsoft/qlib
- https://qlib.readthedocs.io/en/latest/component/data.html
- https://qlib.readthedocs.io/en/latest/component/recorder.html
- https://github.com/microsoft/qlib/blob/main/docs/component/recorder.rst

要点：
- 工作流分层：Data Layer（Provider/Client → Data Handler，带处理器链：标准化/填充等）→ Model → Backtest → Analysis，全部可用一个 `qrun` 命令按配置文件自动跑完（build dataset, train, backtest, evaluate）。
- 因子库标准：Alpha158 / Alpha360 内置 handler（`qlib/contrib/data/handler.py`），DataHandlerLP 挂 processor 链；用户可自定义因子库。
- **QlibRecorder 实验管理系统**：基于 MLflow 的 `MLflowExpManager`，Recorder 状态机 SCHEDULED→RUNNING→FINISHED/FAILED；记录指标、artifacts、模型；配合 `Analyzer` 做结果分析。这是"研究留痕"的开源标杆实现。
- RD-Agent（见下）是其自动化进化延伸。

## 3. RD-Agent(Q)（微软，NeurIPS 2025，自动化因子/模型联合进化标杆）
来源：https://arxiv.org/abs/2505.15155 （arXiv:2505.15155v2, 42页）
代码：https://github.com/microsoft/RD-Agent

要点：
- 五单元闭环：Specification（场景/接口规约）→ Synthesis（基于历史实验轨迹+知识森林生成假设）→ Implementation（Co-STEER 代码生成agent）→ Validation（真实市场回测）→ Analysis（统一指标评估 + **多臂老虎机调度器自适应选方向**）。
- 维护 SOTA 集合；假设生成时同时利用最近反馈与 SOTA 实验（Eq.1 的 action-conditioned 子集）。
- 关键结论：**成本 <$10 的 LLM 调用**，达到比经典因子库高 ~2× 年化收益、因子数减少 70%+——说明"少而精的正交因子"优于"多而杂"。
- 强调可解释性与防幻觉：生成的是可验证的因子/模型代码（跑真实回测验证），不是黑箱信号。
- 失败→结构性调整/引入新变量，成功→增加复杂度/范围：自适应探索策略。

## 4. WorldQuant BRAIN（众包 alpha 流水线，因子质量门禁标杆）
来源：
- https://support.worldquantbrain.com/hc/en-us/articles/5795136028431-Criteria （官方criteria页，403需登录，指标经由多方转述）
- https://www.scribd.com/document/728780335/World-Quant-Brain-Alpha-Documentation
- https://zhuanlan.zhihu.com/p/1915099506304849861 （提交前验证实践）
- https://jglazar.github.io/projects/wq_project/ （IQC 项目描述）
- https://gentlecactus.top/archives/132 （BRAIN平台指南）

要点（D1/D0 区域提交标准，转述值）：
- Sharpe ≥ 1.625（D1）/ ≥ 2.6（D0）；Returns ≥ 6.3% / 8.9%；Fitness ≥ 1.0 / 1.3
- Turnover ∈ [1%, 70%]；Self-correlation < 0.7（与自己已提交 alpha 的 PnL 相关）；Prod-correlation 也有阈值
- Fitness = f(Returns, Turnover, Sharpe) 的综合指标（大致 = Sharpe × sqrt(|Returns|/Turnover) 形式，转述）
- 例外规则：新 alpha 若与已提交 alpha 高相关，但 Sharpe 显著更高，可破例提交
- 平台自动 simulate alpha 对应组合 → 六大绩效指标（Sharpe/Returns/Drawdown/Turnover/Fitness/Margin）打分
- 启示：**因子提交是"硬门禁 + 相关性去重"流水线**，与 RD-Agent 的 Validation Unit 同构。

## 5. 回测过拟合防范：DSR / PBO / CPCV（学术标杆）
来源：
- Bailey & Lopez de Prado (2014) The Deflated Sharpe Ratio, SSRN 2460551: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- Lopez de Prado & Lewis (2018) Detection of False Investment Strategies, SSRN 3167017
- 实现教程：https://www.marti.ai/qfin/2018/05/30/deflated-sharpe-ratio.html
- CPCV/PBO 综述：https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4686376
- https://en.wikipedia.org/wiki/Walk_forward_optimization

要点：
- **E[maxSR]**：N 次独立无技能试验的期望最大 Sharpe ≈ sqrt(V[SR]) × [(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))]，γ≈0.5772。例：日度回测 100 次试验、SR方差 1/252，期望最大年化 Sharpe ≈ 2.5——即纯随机也能挖出 SR 2.5 的"假策略"。1000 次试验 E[maxSR]≈3.26。
- **DSR** = Φ[ (ŜR − ŜR₀)√(T−1) / sqrt(1 − γ₃ŜR + (γ₄−1)/4 ŜR²) ]，其中 ŜR₀ 用 E[maxSR] 公式（以试验方差V与次数N计算）。DSR>0.95 才认为在多重检验校正后仍有真实技能。例：SR 2.5、100试验、1250交易日、偏度-3、峰度10 → DSR≈0.90，仍有 10% 概率完全是假的。
- **Purged K-Fold / CPCV**：训练/验证集之间剔除重叠样本+embargo，防标签泄漏（重叠收益窗口）；CPCV 组合式划法给出 OOS 分布而非单点。
- **PBO**（Probability of Backtest Overfitting）：排列 IS/OOS 排名，若 IS 最优策略在 OOS 处于底部分位则过拟合概率高。
- Walk-forward（WFO）：IS 优化→OOS 前推验证，滚动拼接；**参数超过 4-5 个时 WFO 也防不住过拟合**——参数纪律：能少则少，参数面要平坦（参数邻域性能平稳），不能只有孤立尖峰。
- 样本划分惯例：严格时间序划分 train/valid/test，test 只碰一次；最终留一段"审计样本"（out-of-time audit slice）评估 regime 敏感性。

## 6. 因子自动挖掘学术谱系（进化闭环对标）
来源：
- AlphaGen（KDD 2023, RL 挖协同因子集）：https://github.com/ICT-FinD-Lab/alphagen ；https://dl.acm.org/doi/10.1145/3580305.3599410
- AlphaForge（AAAI，两阶段生成-预测挖掘+动态组合）：https://arxiv.org/abs/2406.18394
- gplearn（符号回归/GP 标准库）：https://gplearn.readthedocs.io/en/stable/
- Warm-Start GP alpha mining：https://www.alphaxiv.org/overview/2412.00896v1
- RD-Agent(Q)：同上

要点：
- 谱系：闭式风险模型(Fama-French) → GP 符号回归(gplearn) → RL 因子组合优化 → LLM 生成式挖掘(RD-Agent/AlphaForge)。
- **协同性（synergy）评估**：AlphaGen 不只看单因子 IC，而是优化"因子集"组合后的表现——因子集层面的目标函数（IC of combined factors），与逐因子独立评估不同。
- 去重都在挖掘循环内做（AlphaGen 的协同训练天然对冗余因子降权；BRAIN 用 self-corr<0.7 硬门禁）。

## 7. 纸面→实盘桥接惯例（非中国平台部分）
来源：
- QuantConnect paper trading docs（同上）
- moomoo/TradingSim/alphio 等交易教育共识：https://moomoo.com/us/learn/detail-what-to-consider-when-shifting-from-paper-trading-to-actual-trading-105622-230490053

要点：
- 业界建议模拟盘 3-6 个月（至少 30-90 天）且达成"连续多月达到收益目标"再上实盘；机构常用更长。
- QC 把 paper 当 brokerage 处理 → 切换零代码改动；上线时显式声明初始资金/持仓继承。
- 通知/告警、崩溃自动重启是实盘部署标配（而非可选）。

## 8. 决策留痕/实验跟踪（MLflow/W&B/Qlib Recorder）
来源：
- https://qlib.readthedocs.io/en/latest/component/recorder.html
- https://wandb.ai/site/experiment-tracking/
- https://github.com/Tussar98/quant-ml-research （production-grade 量化研究框架：WF验证+真实回测+MLflow tracking）

要点：
- 行业标准=实验跟踪三件套：参数/配置版本化 + 指标与artifact记录 + 可复现运行（代码+数据+环境快照）。
- MLflow：开源、自托管、轻量；W&B：托管协作、可视化强。Qlib 直接内置 MLflowExpManager。
- 研究→决策的留痕：每次策略上下线/换版本应有 decision log（谁/何时/依据什么指标/预期影响），类似 ADR（Architecture Decision Record）实践。

## 9. A股微盘/小市值策略的特异性风险（与我们策略直接相关）
来源：
- 2024年1-2月量化危机复盘：https://zhuanlan.zhihu.com/p/682434497 （中证2000单月-21%，微盘踩踏）
- https://www.chnfund.com/article/AR2024022515282476361206 （量化持仓整体偏小微盘、流动性危机）
- https://m.36kr.com/p/2656817840980232 （雪球敲入抽流动性、微盘无量跌停）
- http://m.eeo.com.cn/2024/0224/639051.shtml （72小时量化危机实录）
- 东吴/东财证券小盘研报：https://pdf.dfcfw.com/pdf/H3_AP202404121630186501_1.pdf

要点：
- 2024-01~02：微盘流动性踩踏，量化集体超额大幅回撤（5-10年一遇级别）；诱因=策略拥挤（crowding）+ 雪球产品敲入 + DMA杠杆平仓 + 微盘天然流动性薄。
- 小盘/微盘因子超额本质上有"流动性/壳价值/资金面"beta，拥挤度是领先指标。
- 对我们的直接启示：微盘策略必须有**拥挤度监控、流动性压力测试、容量估算、快速降仓熔断**。

## 10. 个人量化常见错误（中文社区共识）
来源：
- 知乎《盘点量化交易全流程中的30个大坑》：https://zhuanlan.zhihu.com/p/639158715
- 知乎《回测年化100%实盘亏成狗——五大认知陷阱》：https://zhuanlan.zhihu.com/p/2014098758099559459
- 知乎《量化回测中的10大坑》：https://zhuanlan.zhihu.com/p/1973142143271997842
- BigQuant 回测避坑：https://bigquant.com/wiki/doc/sT15bVfKHl

清单（合并去重）：幸存者偏差、未来函数/前视偏差（含"选择偏差型"未来函数）、偷价漏价、交易成本低估（佣金/印花税/冲击成本）、过拟合、小样本运气、忽略涨跌停/停牌可成交性、参数孤峰、回测与实盘滑点差异、无失效退出机制、过度杠杆、微盘流动性容量误判、策略拥挤不监控、单一数据源错误未校验、无对账（实盘持仓与预期漂移）。
