# task-0474 笔记（边查边写）

## 2026-08-23 22:44 启动
- 任务：可转债线去相关强化（正股行业中性化新 E2 预注册），目标 corr(A,组合)<0.5
- 必读：R-289（判门过、corr 0.583 卡点、§6 去相关路径）、R-288（V2 冻结参数）、R-291（B 主候选=可转债、独立性未达标=可修复）、R-262（行业轮动关闭=形态级，正股行业中性化≠行业轮动，不混淆）
- 任务中心 expected_output: shared/results/01-AI行业研究/R-293-可转债去相关强化.md（路径疑为 01/05 笔误；正文按 05-量化投资/ 落盘 R-293 预注册 + R-294 执行报告）
- 数据位置修正：r281 面板实际在 /root/.openclaw/workspace/work/r281/（非 shared/results/work/r281）
  - month_end_panel.parquet（3.7MB）、panel_daily.parquet（25MB）、ic_*.csv
- a13 在役 NAV：/root/.openclaw/workspace/shared/results/04-投资研究/a13_rsraw_e1f10dz_locked_nav.csv（R-289 corr 0.583 用的口径）

## 继续（重试恢复点）
- r467 gate json independence: a13_e1f10dz_locked 0.583 / a13_e1f10_locked 0.583 / i3_abs_s4 0.590 / i3_base 0.585（102月重叠）
- a13 locked nav 止于 2024-06-28（与 2018-02..2026-07 重叠=77 月）；i3 覆盖全窗（102月）
- e2v2_backtest.py 逻辑已读：Top-30 sqrt 梯度、规模中性化 OLS、BUFFER=50、成本 0.001 单边、基准 /tmp/r281/csi_cb_index.parquet
- akshare 1.18.94 可用；panel 1001 唯一 bond code
