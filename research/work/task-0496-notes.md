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

## [00:45] HP 实查 #2：引擎结构与 state 细节
- paper_engine.py 70504B：已有 v3 择时层！get_timing_ratio_safe(:237)；rebalance 内 target_invest = total_assets × timing_ratio；超配 trim（>5% 总资产阈值，整百股）；低配补买 budget gap；TIMING_REBALANCE_MIN=0.35(env PAPER_TIMING_REB_MIN)。**ddc 补丁可复用同一缩放机制（乘法组合），复杂度大降。**
- action_daily(:1312)：回填缺口→当日行（15:05 后东财 spot，否则 parquet qfq）→total/initial=NAV→append_nav→save state。ddc eval 挂点=append_nav 之后。
- 回测 ddc 源码 :528-540 逐字确认：peak_nav=max(peak,cur)（自反馈）；FULL 且 dd≤-0.20→pos=0.5；REDUCE 且 dd≥-0.05→pos=1.0；判定在 NAV 更新后、pos_ratio 影响次日起收益=次日生效。
- paper-state.json(A)：cash=40393, created 2026-08-17, model a13, keys 含 timing_ratio/last_data_date；NAV 仅 7 行，max=1.00892(08-20)，last=0.98319(08-24)，**当前回撤 -2.55%，距 -20% 触发很远**。
- gold paper_state.json：engine_id gold_trend_sma200, status active_paper（2026-08-25 用户批准激活，影子期豁免）；frozen_form: sma200/vol60/target10%/cost0.13%/monthly(first trading day)/MMF 000198；current_weight=0.0；last_signal(2026-07-31): px 8.433 < sma200 9.479 → w=0；但 08-24 px=9.564 > sma200≈9.479，**9/1 首调仓大概率转多，w≈0.1/0.2201≈0.45**；nav_policy: 新链 2026-08-24 起 NAV=1.0，157 月史由 shadow_nav 承载。
- MMF 口径：月度结账用 mmf_monthly_push.csv（VPS 月推），**断供≥2月=终止判据 c3**；日内现金腿线性估计（<1bp/月误差），月结重述。黄金腿 518880 腾讯 fqkline。
- R-284 §四 选项A 原案（本方案 §4 直接衔接）：daily 动作算 NAV vs HWM；≥15%→×0.5；收复≥5%→恢复；状态持久化；参数走 main.json params（drawdown_control/dd_thresh/dd_reduce/dd_recover 同名同义）；生效=下个 16:30 cron 自然生效（crontab 零改动）；回滚=tar 还原。**血统缺口②「a13+ddc 从未回测」已被 R-316 口径1 补上（17.6%/-14.2%/Calmar1.245）**。注意 R-284 时是 ddc15，F6 拍板用 dd_thresh=0.20。

## [00:48] 设计决定（全部写入报告，含被否选项）
1. 架构=α 中央补位器独立脚本 + A 腿最小 ddc 补丁 + gold 腿零改动。否 β（A 引擎内嵌：耦合最大、动在役引擎回滚最重、gold 信号时序耦合）与 γ（gold 引擎扩权：刚 active 即大改违激活纪律、运动员兼裁判）。
2. 层2 记账=两只基金账面份额模型（口径L）：NAV_L2 = A_total + sleeve；sleeve_value = backfill_notional × NAV_G(t)/NAV_G(t_transfer)；**backfill_notional = total_A×(1-ddc_scale)（仅 ddc 释放部分；择时低配现金不补位——与回测 w̄A=ddc pos 严格一致，易做错点）**。paper/shadow 阶段纯账面（gold 引擎零感知）；真金阶段换镜像执行（层2 自持 518880 跟 gold w）。被否：给 gold 引擎加申购接口（动在役 gold 引擎+破坏 NAV 审计连续性）。
3. ddc 判定位置=A 腿补丁内置（权威，受控净值自反馈要求 NAV 含缩放效应）；层2 只读 state，禁自算（防双源真相漂移）。影子阶段补丁只写 ddc_shadow_log 不执行。
4. 时序：A daily 16:30 UTC（T 收盘后）eval T 日 NAV→pending；T+1 daily run 执行 @T+1 收盘价=回测次日生效逐位同构。层2 cron 建议 50 16 * * 1-5（16:50 UTC，A daily 之后、两引擎都已完成；周五 A daily 若拖长则 mtime 检查重试）。
5. 补丁函数级：eval_ddc/apply_ddc_scale_trade/get_ddc_scale + state.ddc 块 + main.json params（默认 drawdown_control=0）+ rebalance 一行乘法组合。约 80-120 行。
6. 阶段：0 批准（9/1 冻结，9/5-9/6 窗口）→1 A 腿补丁+影子 7 交易日（用户门：动在役引擎）→2 层2 账本影子 ≥1 月含两次月调仓（用户门：crontab）→3 真金切换（用户门：比例/结构拍板；建议等名义双层，F6 增值层与 F7a 底仓层不互斥——R-317）。
7. 偏差分析 7 条（月频 vs 日频补位时点、收益源、成本方向有利、触发漂移 a15 ±3 周先例、择时交互同构（乘法可换）、gold 可得性 c3、真金现金腿 MMF 简化 -0.3%/年×占比）。
8. 风险 10 条（竞态、c3 冲突、漂移、n=1 过拟合、9/1 窗口、补位口径误做、双源真相、sleeve 时点、回补执行残现、写权限隔离）。
