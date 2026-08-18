# task-0374 notes — A12 阶段A 大小盘轮动×择时四方案引擎级回测

## 0. 任务与口径

- 任务：S1-S4 四方案计算落盘（不写正式报告），对拍 + 回测 + notes。
- 引擎口径：复刻 `e2_eng_timing.py`（task-0362 已验证对拍方法论）：单遍 v5h 选择路径 + 后验递推，微盘腿成本=调仓日逐股 ADV20 冲击（无条件计收，≡e2 对拍口径），择时缩放不计独立换仓成本。
- 轮动语义（R-236 窄口径）：**轮动腿只进持仓态**（q3z regime on，tr∈{0.6,1.0}），空仓态（tr=0）保持现金。
  - 日收益公式：`eff = tr × (w × r_micro + (1−w) × r_large) − engine_cost − switch_cost`
  - r_micro = 引擎选择路径日收益；r_large = Mlarge_top20 等权日收益（task-0365_series.parquet，md5 校验传输）。
  - 切换成本：`40bp × |Δw| × tr`（双边 40bp=每边 20bp）；S1_sw0 零成本敏感性；S1b 引擎成本按 w 缩放敏感性（均不计数）。
- 信号 shift1（t 收盘→t+1 生效），S2/S3 强制窗 15td（复用 e2 hold_window+首日限定口径）。
- 分段：locked 2006-01~2024-06 / holdout 2024-07~2026-08 / s1 / s2；n_trials=4（S1-S4）。
- 对照：v6a_def（引擎锚 14.63/-24.67 locked）；v5h_xsub 参考线 15.74/-29.80。
- 血统线：locked 年化 +2pp 且 MDD 恶化 ≤2pp。

## 1. 素材核验（已完成）

- R-236：D/E 门内轮动载体级 ann 16.9-17.1% vs B 14.5%（2016-2026 段）；F 空仓换大盘证否（MDD -66.3%）；re-entry 弱（切回 micro hit15 46-52%）。
- R-233：REB 不做全仓门（A_REB MDD -52.6%），但 holdout +3.8pp → S2 用作持仓态内方向调制；C 危机首日 13 段集中真危机日。
- task-0365_series.parquet：5030 行（2005-12-01~2026-08-14）；micro_state_ma60=True 为 micro 态（2024-01-15 切 large 已复核与 R-236 episode 一致）；Mlarge 为净值级数（pct_change 转日收益）。
- 引擎脚本 `scripts/a12_rot_engine.py` 已 md5 校验部署 HP，py_compile 通过；nohup 后台运行（logs/a12_rot_engine.log）。

## 2. 方案定义（执行口径）

| 方案 | w_micro 定义 |
|---|---|
| S1_rot | micro_state_ma60（RS vs MA60，1=micro/0=large）shift1 |
| S2_reb | S1 + REB_bottom 触发→持仓态内强制 w=1 持 15td |
| S3_crisis | S1 + C 危机首日→无视 RS 强制微盘 15td |
| S4_grad | RS 20 日滚动分位（含当日）连续映射 0-1，shift1 |

## 3. 对拍与结果（待运行完成后追加）
