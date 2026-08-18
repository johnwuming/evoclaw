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

## 3. 对拍结果（PASS）

- ANCHOR OK：MA15_base locked ann 0.146300 = ref 0.146300；locked mdd −0.246700 = ref；diff_full/diff_locked 均空；nav vs `a9_timing_MA15_on_f0_nav.csv` max|Δ|=1.78e-15 < 1e-14。
- 运行：HP nohup 131.5s（市场加载 70s + 选择路径 56s + 变体 6s）；选择路径 5008 日 / 248 调仓（与 e2 一致）。

## 4. 四方案主表（引擎级，含成本；成本口径见 §0）

| 变体 | full ann | full MDD | Calmar | locked ann | locked MDD | holdout ann | holdout MDD | s1 ann | s2 ann | 腿切换 | 年换手 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MA15_base（锚） | 14.48% | −24.67% | 0.587 | 14.63% | −24.67% | 12.95% | −13.50% | 21.22% | 7.91% | 0 | 0 |
| S1_rot | 14.81% | −25.36% | 0.584 | 13.65% | −25.36% | **25.27%** | **−8.20%** | 22.18% | 7.65% | 119 | 11.6 |
| S2_reb | **15.55%** | −25.16% | **0.618** | 14.47% | −25.16% | 25.32% | −8.20% | 22.16% | 9.10% | 109 | 10.6 |
| S3_crisis | 14.88% | −25.93% | 0.574 | 13.73% | −25.93% | 25.26% | −8.20% | 22.25% | 7.73% | 116 | 11.3 |
| S4_grad | 12.05% | −26.66% | 0.452 | 11.83% | −26.66% | 13.79% | −8.96% | 19.76% | 4.60% | 15 | **25.4** |
| S1b_costscaled（敏感） | 15.28% | −24.71% | 0.618 | 14.11% | −24.71% | 25.83% | −8.20% | 22.65% | 8.12% | 119 | 11.6 |
| S1_sw0（敏感） | 17.23% | −24.91% | **0.692** | 15.97% | −24.91% | 28.71% | −8.20% | 24.15% | 10.49% | 119 | 11.6 |

对照参考线：v5h_xsub 15.74/−29.80；v6a_def locked 14.63/−24.67（=本表锚，逐位复现）。

## 5. 核心发现

1. **holdout（2024-07~2026-08）轮动大幅兑现**：所有 S1-S3 变体 holdout ann ≈25.3% vs 基线 12.95%（**+12.3pp**），MDD 同步改善（−8.20% vs −13.50%）。这是 2026 流动性枯竭段 RS 持续 large 态（R-236 证据五）的引擎级兑现——风格分化防护价值成立。
2. **locked 段血统线不达标（全体）**：最佳 S2_reb ann −0.16pp（基本持平），S1 −0.98pp，S4 −2.8pp；MDD 恶化均 ≤2pp（该项达标）。分段归因：s1(06-16) 轮动增益 +0.96pp（零成本 +2.9pp），s2(16-26) 轮动拖累 −0.26pp 且 MDD 恶化 2.9pp——与 R-236 载体级 s2 +2.5pp 结论**方向相反**，根因是载体级近似门（日频 Mmicro>MA15+零成本+无 q3z regime）与引擎口径（月频 q3z×trend+ADV20 成本）差异，再次验证“载体级类比不可替代引擎口径”。
3. **成本是 locked 段拖累主因**：S1_sw0（零切换成本）locked 15.97%（+1.34pp）vs S1_rot（40bp）13.65%；线性内插 S1 盈亏平衡切换成本 ≈23bp。S1b（引擎成本按 w 缩放的经济口径）locked 14.11%，介于两者之间。
4. **S2（REB 方向调制）是最优主口径方案**：full Calmar 0.618 > 基线 0.587；把 S1 的 locked 拖累从 −0.98pp 修复到 −0.16pp（REB 触发窗强制微盘 15td 抵消了部分 large 态换手），s2 +1.19pp，holdout 增益全额保留。验证 R-233 “REB 不做全仓门、可作方向调制”结论。
5. **S3（危机回切）无增益**：locked −0.90pp、MDD 多恶化 1.26pp；C 首日 13 段触发（≥5 可上岗门槛达标）但方向性微弱——危机 V 底抄微盘在引擎口径下不成立。
6. **S4（梯度权重）证伪**：20 日分位连续权重年换手 25.4×，40bp 切换成本年拖累 ≈10pp（12.05% vs 基线 14.48%）；即使 MDD −26.66% 逼近恶化上限也无收益补偿。连续映射若要复活需大幅降频（月频采样或带宽迟滞），非本轮范围。

## 6. 触发/换手/容量披露

- REB_bottom：112 日 / 97 段（S2 用）；C 危机原始 18 日/16 段，首日限定 13 日/13 段（S3 用，≥5 达标）；RS ma60 状态：micro 2118 日 / large 2890 日（large 态占 58%）。
- 腿切换次数：S1 119 次 / S2 109 / S3 116 / S4（二元口径）15；年化腿换手 S1 11.6 / S2 10.6 / S3 11.3 / S4 25.4。
- 成本假设：腿切换双边 40bp（每边 20bp）；大盘腿 Mlarge_top20（约 1080 只前 20% 市值等权）流动性充裕，容量瓶颈在微盘腿（引擎 capital_base=1e7，ADV20 冲击模型，与 v6a_def 相同）。
- 触发 <5 次不可上岗检查：S2/S3 触发源均 ≥13 段，无此问题；S4 无触发概念（连续权重）。

## 7. n_trials 登记

- 本轮 n_trials = 4（S1/S2/S3/S4）；S1b_costscaled、S1_sw0 为口径/成本敏感性不计数。
- 结论走向建议（供阶段B正式报告）：S2_reb 为保留候选（full Calmar 最高、locked 基本无损、holdout 大幅增益）；S1 需降切换成本或降频再验；S3/S4 归档。locked 血统线（+2pp）未达成——正式晋升判断需结合 holdout 分化防护的存在性证据单独权衡，不在本阶段下结论。

## 8. 产物清单

- `shared/results/work/task-0374-out/a12_stats.json`（统计，md5 与 HP 一致）
- `shared/results/work/task-0374-out/a12_nav_daily.csv`（5008 日 × 7 变体日频净值）
- `shared/results/work/task-0374-out/a12_pos_daily.csv`（w_micro 日频权重 × 7 变体）
- HP：`results/timing_v2/a12_{stats.json,navs.csv,pos_micro.csv}`、脚本 `scripts/a12_rot_engine.py`、日志 `logs/a12_rot_engine.log`
- 输入：`results/timing_v2/a12_rot_series.parquet`（=task-0365_series.parquet md5 校验传输）
