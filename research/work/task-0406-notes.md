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
