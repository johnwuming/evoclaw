# task-0496 R-318 F6 中央风控层2 实施方案设计 — 过程笔记
# 开始: 2026-08-26 00:35 GMT+8 | 零生产改动（HP 只读，VPS 只写 work/+报告）


## [00:37] 基础材料1：R-316 要点（已全文读）
- F6 定义：A 引擎满仓运行，ddc（dd_thresh=0.20, dd_reduce=0.5, dd_recover=0.05）触发降仓时，释放的 0.5 仓位资金补 gold 引擎，总仓位恒满。
- ddc 源码语义（HP backtest_dividend_quality_iter.py :533-540）：
  - 满仓 且 受控净值/运行高点-1 ≤ -0.20 → 仓位×0.5（次日生效）
  - 降仓中 且 回撤收窄 ≥ -0.05 → 回补满仓
  - 回撤基准=受控净值自身高水位（自反馈）；日频收盘判定；PIT 安全
- 回测：年化 19.1%/mdd -14.0%/Sharpe 1.197/Calmar 1.370；触发事件窗口内仅 1 次（2015-06-29→2020-06-19，1817 天，61 个补位月，事件期补位贡献 +16.9pt NAV）
- 交叉验证：仿真状态机触发日与 HP 已跑 a15_ddc20 实跑一致（降仓日完全一致；回补 2020-06-19 vs 2020-07-08，差 3 周，a13/a15 净值差异所致）
- 关键机制：受控净值自反馈 → 半仓期净值爬慢 → 回补慢（事件可持续 5 年）
- gold 补位口径：降仓资金按月吃 gold 引擎整体月收益（w_gold=1-w̄A，月频近似）——实盘为事件驱动日频，需做偏差分析

## [00:37] 基础材料2：R-317 要点（已全文读）
- F7a（等权打底+降仓全补黄金）作对照：Sharpe 1.483/Calmar 2.001/mdd -6.80%，收益与 F1 持平
- R-316 F6 补位价值对账口径：0.5 权重 × 61 月 ΣrG≈33.6% ≈ +16.8pt
- 状态机 PIT 做法：月 t 权重由 t-1 月最后交易日收盘状态判定；代码内建 assert（2015-06=FULL、2015-07=REDUCE、2020-06=REDUCE、2020-07=FULL）
- F7 引擎验证法：非 episode 月与 F1 月收益逐位相等（0 个不等月）——等价性验证范式可复用到 F6 实施门
- 已记录风险：生产 A 引擎实时 nav 与全回测 nav 有差异，触发日会漂移（a15 实跑回补差 3 周）
- 局限声明：n=1 episode；gold 为影子链月频 net

## [00:38] task-0459 脉络（memory/2026-08-23~25）
- 0459 发现：paper_engine.py（63KB 自包含，16:30 UTC cron）无 ddc 代码路径；ddc 只在回测引擎 backtest_dividend_quality_iter.py。
- 用户三选项（R-284 §四）：A=paper_engine 最小 ddc 补丁（0.5-1人时，血统路线 a15_ddc15 整体 vs a13+ddc 补回测须一并定）；B=应急预案常备（已选）；C=charter 近似（不推荐）。
- 当时选了 B（决策B常备已闭环）；本次 F6 拍板 = 选项 A 的正式激活路径。
- 0459 附带发现：ddc 价值集中在 2008/2015 深熊，不在 v1.2 冻结危机清单；O1b 叠加轨三线全败。
- 还有 task-0461「paper 修复」已完成——需查 memory 确认修了什么（可能与本方案有关）。

## [00:40] HP 实查 #1：基线 mtime（零改动声明 BEFORE 基准）
- scripts/paper_engine.py = 70504B, mtime 2026-08-24 22:27:57 UTC（task-0461 paper 修复所致）
- scripts/paper_engine_gold.py = 16474B, mtime 2026-08-24 16:55:31 UTC
- model/registry/engines.json = 14649B, mtime 2026-08-24 16:56:23 UTC
- scripts/backtest_dividend_quality_iter.py = 36116B（ddc 语义参照）
- crontab（只读列出，未改）：
  - A 链：30 16 * * 1-5 daily；0 15 * * 1-5 rebalance --check-month-start；0 20 * * 0 validate
  - gold 链：40 7 * * 1-5 paper_engine_gold.py daily；0 3 * * 0 verify
  - gold 影子月任务：38 9 3 * * append shadow_nav；40 9 3 * * evaluate
- registry engines.json：top=[schema_version, engines(list)]；3 引擎：A a13_rsraw_e1f10dz=active；T4 crowdf2=shadow；gold（SMA200×波动目标10%×月频×现金增强）=active（=正式监控态）
- 无 active_paper 键（任务书描述"active_paper w=0"应指 gold 引擎 paper state 内字段，下一步实查）
