# 调研底稿：因子管理与回测标准（R-204）

## 因子生命周期（米筐 RiceQuant 因子系统）
- 状态流：创建中 → 测试/验证 → 上线/入产品库 → 下线
- RQFactor：从"因子创建"到"有效性验证"的落地操作：计算基础因子→IC/IR分析→组合测试
- BigQuant BigAlpha 因子库：上架审核 → 发布 → 下架（社区共享模式）

## 因子评价指标（行业用法）
- IC（Information Coefficient）：因子值与下期收益的截面相关系数（Rank IC = 因子排名与收益排名相关），衡量预测能力；|IC| 越大越有预测力
- ICIR（= IC均值/IC标准差，又称IR）：衡量因子预测稳定性；行业参考：IC > 0.03~0.05、ICIR > 0.3~0.5 才算有实际可用性；Alphalens 惯例参考 IC>0.07、IR>0.4
- 覆盖率（coverage）：因子在股票池中有效值的比例，需满足最低覆盖（如 >80%）
- 换手率（turnover）：因子多头组合调仓的换手，影响实际交易成本
- 十分法分组单调性：按因子值十分位分组检验收益单调性（聚宽因子研究系列的标准流程）
- 市值分层稳定性：因子在高/中/小市值内的区分度与稳定性检查（聚宽）
- 相关性矩阵：因子两两相关，剔除高相关冗余（如 |corr|>0.7 视为冗余）

## 因子正交化/去重（行业做法）
- 剔除冗余：相关性矩阵 + 聚类（如层次聚类）后每簇留代表因子
- 正交化：对市值/行业等风险因子做回归取残差（行业中性化、市值中性化）
- 新增因子须与已有活跃因子相关性检查：WorldQuant 要求 self-correlation < 0.7 才算"新"
- 严格流程：每只新因子先过"低相关性"检查再进候选池

## 回测验证体系（机构标准）
- Walk-Forward Analysis（WFA）：滚动训练+样本外测试循环，模拟真实再优化决策过程；机构最常用的验证框架
- Walk-Forward Efficiency（WFE）= 年化样本外收益 / 样本内收益，衡量策略优化在样本外兑现的程度
- Purged K-Fold CV + Embargo：清除训练/验证时间重叠，避免泄漏（López de Prado, AFML）
- CPCV（Combinatorial Purged CV）：生成多条 OOS 路径，估计 PBO（Probability of Backtest Overfitting）
- Deflated Sharpe Ratio（DSR）：校正多重检验选择偏倚（试验次数N需显式记录）
- 多重检验修正：按尝试次数N调整显著性阈值（Bonferroni/DSR），量化研究须"显式记录所有试过的假设"
- 参数寻优纪律：机构惯例为"有限参数格点 + 整段样本内寻优 + 严格留出的样本外验证"，反对无限制网格搜索
- 样本内外划分：时间序列必须按时间切分（训练在前、测试在后），且测试段不参与任何选择

## 模拟盘→实盘桥接（行业惯例）
- 米筐：回测 → 实时模拟（Level-1 实时行情驱动，约3-5秒延迟）→ 实盘；模拟与实盘同引擎（RQAlphaPlus）
- 聚宽：必须先回测通过 → 才能创建模拟交易；模拟盘换代码仅限对应回测详情（防未来函数）
- 聚宽不支持实盘下单，需外接 QMT/PTrade 券商终端
- 跟踪误差/差异监控：回测 vs 模拟 vs 实盘三者绩效差异追踪（交易成本、滑点、成交假设）
- Alpha Decay 检测：策略超额收益随时间衰减；检测指标包括超额收益滚动均值、信息比衰减、收益分布偏移、regime change 检测（CUSUM/贝叶斯切换点）

## 来源链接
- 米筐因子生命周期: https://www.ricequant.com/doc/quant/factor-system
- RQFactor: https://www.ricequant.com/doc/rqfactor/manual/index-rqfactor
- 聚宽 jqfactor_analyzer: https://github.com/JoinQuant/jqfactor_analyzer
- 聚宽因子研究系列: https://www.joinquant.com/view/community/detail/3794
- BigQuant BigAlpha: https://bigquant.com/wiki/doc/EOVmVtJMS5
- WFA (BigQuant): https://bigquant.com/wiki/doc/gVpC1nnxVS
- DSR论文: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- 回测陷阱 (quant67): https://quant67.com/post/quant/20-backtest-pitfalls/20-backtest-pitfalls.html
- Alpha Decay: https://www.vertoxquant.com/p/strategy-decay-detection
- 微盘股风险: https://paper.cnstock.com/html/2026-07/20/content_2246221.htm
