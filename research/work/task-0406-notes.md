# task-0406 过程笔记（R-250：拥挤度×选股 + RV×择时 E1 画像）

开始：2026-08-21 00:36。预算 ≤40min。
任务中心 task-0406 已置 running（00:35）。

## R-249 定义摘录（来源：R-249 §三）
- 方向三（拥挤度进选股降权）：先做 crowding_history.csv 与选股时点 PIT 对齐审计（防未来重算值），画像 = crowding 状态 × 月度选股收益（条件收益/MDD），达线才引擎级。E1 门槛（R-231）：触发数 ≥20 + 分段胜率方向正确。
- 方向四（RV 进择时层）：RV 日频自算（月频采样），画像 = 高/低波动状态 × 择时层（q3z×EW-MA200 在役信号）条件收益/回撤；与 ddc15/ddc20 做冗余度初查（同高回撤段触发重叠度）。达线 → E2 预注册（乘法门、非全仓门、非事件门）。
- 择时在役信号：q3z×EW-MA200（A 系列在役 a13_rsraw_e1f10dz 相关）。

## 计划
1. HP 实查：crowding_history.csv 位置/结构/时间范围
2. 日线面板位置（task-0402 日更的 qfq parquet）
3. 月度调仓/收益记录（paper ledger、A 系列回测 ledger）
4. PIT 审计（拥挤度采集时点 vs 选股时点）
5. 画像脚本 → HP nohup 跑 → 落盘中间产物
6. RV 自算 + 状态画像 + ddc 冗余度
7. R-250 报告 + README 更新

## 边查边记
（逐步追加）

## 实查结论（00:36-00:42）
1. crowding_history.csv = HP ~/quant-evolve/results/crowding_history.csv，269,852B，**实际 2019-01-02 起**（任务书写"2006起"与实况不符，画像窗口=2019-01→2026-08 ≈ 92 个月，E1 样本量按此评估）。8 列：micro_turnover_share(_roll20/_monthly)、micro_turnover_mean、micro_turnover_pct60、excess_slope_60d(_tstat)、snowball_dist_zz500_12m。由 collect_crowding.py 全本地自算（akshare 不可达时）。
2. **PIT 审计**（collect_crowding.py L169-200 实读）：
   - 全部窗口后视：rolling(20)、rolling(ROLL).apply(pct_rank60)（x<=x[-1] 即当前值在 trailing 窗口分位）、shift(252)——构造无前视。
   - micro_turnover_share = 微盘成交额/全市场成交额（amount 口径，qfq 复权无关）→ 主画像口径用它，PIT 稳健。
   - 残余风险：①宇宙划分按总市值（收盘×总股本，qfq close）排序后20%，qfq 复权因子更新会改写历史市值排序 → 历史值随全量重算漂移；②文件仅一份无历史备份，漂移幅度不可直接验证；③excess_decay 用 qfq 微盘指数 vs hs300 累计超额，同样受复权改写影响。→ 结论：成交额口径指标可作 E1 主口径，市值排序漂移风险如实披露，E2 前若需引擎级须先落"月度快照"机制。
3. A13 回测产物：a13_rsraw_e1f10dz_full_nav.csv（2006-01-04→2026-08-14，5008 日；248 次调仓≈月频；metrics: annual 0.2239, MDD -0.3355, drawdown_control=0 即本体无 ddc）。
4. 择时层：timing_v2/a12_pos_micro.csv 的 MA15_base 列 = 每日仓位 0-1（q3z 连续仓位在役形态），2006→2026-08-14。signal_series.parquet 含 M_micro_ew（微盘等权日指数，2006-01-05→2026-08-07，5003 日）→ RV 自算源。
5. ddc15/ddc20：a15_ddc15_full_nav.csv 仅 date/nav/num_held 无仓位列 → 冗余度用「A13 策略 dd≤-15%/-20% 阈值日」作 ddc 触发代理（ddc 组件语义即策略回撤阈值门）。
6. paper-nav.csv 仅 3 行（paper 引擎新近启动），历史画像用 A13 回测 ledger。

## 画像设计（已落脚本 scripts/r250_profile.py，HP PID 497026，日志 logs/r250_profile.log）
- 方向三主口径：share_roll20 expanding 分位(min250d, PIT) → high≥70/mid/low≤30 × 次月 A13 收益（均值/胜率/月内MDD/危机月数）；副口径 pct60。
- 方向四：RV20=ln(M_micro_ew) 滚动20日std×√252 → trailing756d 分位 → × 择时态(MA15_base<0.99=de_risk) 3×2 网格；关键格=high-RV+full（门漏掉的高波月）。日频 forward20d 收益对照。
- 冗余：rv_pct≥0.7 日 vs dd≤-15%/-20% 日重叠（Jaccard/条件概率）。
- 产物：~/quant-evolve/results/r250/{crowding_monthly.csv, rv_monthly.csv, r250_summary.json}

## 画像结果（v1+v2，产物 r250_summary.json / r250_v2_summary.json，已拉回 VPS work/r250/）
### 方向三（拥挤度，80 个月样本 2020-01→2026-08）
- 主口径 expanding pct 70/30：high n=5 / mid 30 / low 45；high 均值 0.45% vs low 1.36%（方向对，差 -0.91pp/月）但 n=5 <20 → 未达线。
- 敏感性 roll3y(756d) pct 70/30：high n=15（<20），high 0.22% vs low 1.36%。
- 敏感性 roll3y 60/40：high n=20（=20 临界），high 0.43% vs low 1.57%（差 -1.14pp/月），胜率 0.60 vs 0.70，月内MDD均值 -2.2% vs -3.4% → 方向正确、触发数临界达标。
- 副口径 pct60：方向反转（low 月份均值 -0.64% vs high +1.86%）→ 单指标内部口径分歧，稳健性不足。
- 旗舰案例：2023-09→2024-01 roll3y_pct 83-93 持续高位，2024-01 mkt_ret -24.2%（A13 仅 -4.2%，择时层护住）→ trailing3y 口径在 2024-01 踩踏前确实处于高位。
- 判定：**有条件达线**（仅 roll3y 60/40 临界过线；主口径未过）→ E2 预注册建议附带两个前置条件（见报告）。
### 方向四（RV×择时，235 个月样本 2007-01→2026-08）
- 市场层 fwd20d（择时无关）：rvhi +2.10%（n=1358日）vs rvlo +0.77%（n=1500日）→ 高波后市场前向收益更高（均值回复），与「高波降仓」假设方向相反。
- 3×3 网格关键格：rvhigh|poshigh n=7 均值 +7.72%（反弹月，砍仓即砍收益）；rvhigh|poslow n=26 均值 -0.51%（在役门已降仓的月）；rvlow|poshigh n=31 均值 +5.24% 胜率 96.8%（最佳格）。
- 冗余度（日频）：dd≤-20% 日 197 天中 85.3% 处于 RV-high（rv_pct≥0.7，1358 天）；Jaccard 0.12/0.22 → ddc 深回撤触发几乎全被 RV-high 包含 → 真危机段高度冗余，而 RV-high 大部分时间不对应深回撤（p(dd20|rvhi)=12.4%）。
- 判定：**未达线**（分段胜率方向不成立 + 与 ddc 深回撤段冗余 85%）→ 负结果如实记录；RV 冻结为状态监控变量。rvlow|poshigh 观察性亮点标注为事后格子挖掘，不作 E2 建议。
### 计算/验证记录
- HP 计算进程 PID 497026（v1）已自然退出 code 0；v2 同步跑完。未动 registry/pipeline/paper_engine/crontab，未杀任何既有进程。
- 中间产物：HP ~/quant-evolve/results/r250/（5 文件）+ VPS shared/results/work/r250/（同 5 文件镜像）。
