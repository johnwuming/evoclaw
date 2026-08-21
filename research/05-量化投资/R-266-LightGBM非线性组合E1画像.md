# R-266 LightGBM 非线性因子组合 E1 画像（task-0414 / R-249 方向二·阶段A）

- 日期：2026-08-21
- 任务：task-0414（research，阶段A=E1 层，零回测）
- 结论一句话：**LightGBM 替换 ranksum 合成器在同口径 186 个月 walk-forward 下复合 ICIR 0.750（默认组）/ 0.717（搜索组），较 ranksum4 基准同窗 0.667 增量 +0.084 / +0.050，未达预登记门槛 +0.15；五分段无方向翻转、五分位单调，但增量不足 → 不建议进 E2 预注册，负结果归档。** 与 R-249 低预期（引擎级 0-2pp）一致。

## 一、背景与目标

R-226 P2 / R-249 方向二：ranksum 线性序数合成可能损失因子交互信息，用 LightGBM 提取残余非线性信息。本任务为阶段 A（E1 层）：只做数据可用性评估 + IC 画像，达线才进 E2（预注册另任务）。防过拟合纪律（R-226 加倍）：walk-forward 严格时间分离、超参 ≤2 组预登记、种子固定、试验全程计账、特征只用现成数据。

## 二、数据债评估（阶段A第一交付，实查数字）

### 2.1 fin_deep 面板（data/derived/fin_deep_monthly_panel_ak.parquet，3,004,665 行 × 24 列）

- **无末端截断**：ym 覆盖 2005-06 ~ 2026-08，每月 11,783 行（含退市）；所有列"nonnull≥30% 的最后月份"= 2026-08。
- **新鲜度正常（季节性而非断裂）**：逐月值变动计数呈财报披露季节性——gp_margin 变动数 2026-04/05 为 10,133/11,065（年报+一季报集中披露），2026-06/07 仅 224/275（淡季），2026-08 回升 1,002（中报开始）。R-235 所记"末端缺失"在当前面板已不存在（或指当时已修复的抓取断档）。
- **真实数据债是广度覆盖**：现金流量表系列（accrual_quality / cf_or_ratio / cf_np_ratio / ocf_stability / dupont_asset_turn / dupont_leverage / dupont_tax_burden / debt_to_asset / cash_to_asset / inventory_to_asset / ar_to_asset）近月 nonnull 仅 **44.5%**（全史 27%）；利润表系（gp_margin / roe_report / revenue_yoy / net_profit_yoy / profit_accel）近月 95-99%。若未来 ML 扩特征到 cash-flow 列，约半数股票缺失（LightGBM 可原生容 NaN，但需评估选择偏差）。
- **对本试点影响：零**。预登记 8 特征不含 fin_deep 列（见 2.2），绕行方案无需启用。

### 2.2 特征可用性（107 因子面板 vs W1 口径）

107 因子面板（v3ak 机制）可用月 2006-01 ~ 2026-07、IC 月 246 个、全 A 口径。预登记 8 特征与来源：

| 特征 | 107 面板是否现成 | 实际来源 |
|---|---|---|
| log_mv | ✓（circ_mv 取 log） | K 线月末收盘 × outstanding_share |
| log_amt20 | ✗ 自建 | K 线日额 20 日滚动均值（月末锚） |
| pb_inv | ✗ 自建 | ths_ttm_panel.equity 按 avail_date PIT as-of 月末 → equity/circ_mv = 1/pb（与在役 merge_pb_into_panel 同式） |
| roe_ttm | ✓ | ths_ttm_panel PIT as-of + ffill |
| ret_20d / ret_60d | ✓ | K 线 20/60 日收益（月末锚） |
| vol_60d | ✓（近义 mv_volatility_60d） | 日收益 60 日 std |
| turn_20d | ✓（近义 turnover_rate） | 日换手 20 日均值 |

面板 md5 `738727d38aec682da725db7ba8be0391`：5206 股 × 247 月 × 8 特征，合格池 693,194 行月，mask 内特征覆盖率 99.3-100%。PIT 细节：as-of 锚用每月 28 日（保守：月末 29-31 日披露的财报顺延下月生效，杜绝前视）。

## 三、方法（预登记后冻结）

- **IC 口径（W1 复刻）**：IC[m] = spearman(F[m], R[m+1])，月频全市场，min_obs=20；合格池 = 上市≥120 交易日、月收盘>0、月成交>0。
- **ranksum4 基准**：Σ sign·rank_pct 等权（log_mv −、amt20 −、pb_inv +、roe_ttm +），同面板同口径重算（240 月 ICIR 0.6893，与 R-264 g0 参照量级一致）。
- **walk-forward**：预测月 m，训练特征月 j ∈ [m−60, m−1]，样本 (F[j], R[j+1])——最晚训练标签 R[m] 于月末预测时点恰好可得，**严格无泄漏**（边界：首预测月 2011-01，训练窗 2006-01~2010-12，打分 F[2011-01]，目标 R[2011-02]）。月频推进 186 个预测月（2011-01 ~ 2026-06）。训练窗末 12 月作早停验证集。
- **超参两组**：D = num_leaves 31 / lr 0.05 / n_estimators 300 / min_child 200 / ff 0.9 / bag 0.8；O = 预登记空间随机搜索 **20 trial**（seed 42）在首训练段选定后全程冻结 → num_leaves 15 / lr 0.03 / min_child 200 / ff 1.0，val_ic 0.0831。**偏差如实记录：optuna 未安装且不装（防依赖升级动生产 env），用固定种子随机搜索替代，trial 计账同口径（全程合计 20 trial + 0 组外调参）**。
- 种子 42；截面预处理 = 逐月 1%/99% winsorize + zscore（R-251 隔离测试：不改秩 IC）。

## 四、核心结果

### 4.1 主判定表（同窗 186 月，2011-01 ~ 2026-06）

| 配置 | mean IC | ICIR | ΔICIR vs ranksum | IC>0 | 五分段 ICIR | 五分位单调 |
|---|---|---|---|---|---|---|
| ranksum4 基准 | 0.0858 | 0.667 | — | — | 0.73/1.33/0.32/0.75/0.50 | ✓ |
| LightGBM-D | 0.0898 | **0.750** | **+0.084** | — | 1.23/1.19/0.30/1.08/0.58 | ✓ |
| LightGBM-O | 0.0908 | **0.717** | **+0.050** | — | 1.17/1.14/0.22/1.08/0.60 | ✓ |

（基准全窗 240 月 ICIR 0.6893；同窗截取后 0.667，两口径均低于门槛差。）

### 4.2 五分位分组（组内等权月均次月收益）

- ranksum4：Q1→Q5 = 0.51% / 1.15% / 1.63% / 2.14% / 2.42%（价差 1.91pp）
- LGBM-D：0.01% / 0.63% / 1.06% / 1.44% / 1.91%（价差 1.90pp）
- LGBM-O：0.06% / 0.67% / 1.00% / 1.37% / 2.00%（价差 1.94pp）

三者均严格单调，但 LGBM 的分组价差并不优于基准——ICIR 增量主要来自 IC 波动略降（std 0.129→0.120）而非排序尾部区分度提升。

### 4.3 信息增量与近年表现

- LGBM 与 ranksum 的 IC 序列相关 0.77（D）/ 0.78（O）→ 约 22-23% 正交信息，但未转化为足够 ICIR 增量。
- 2018+ 子窗（102 月）：ranksum ICIR 0.563 vs LGBM-D 0.641（+0.078）；2021+ 子窗：ranksum 0.646 vs LGBM-D ≈0.63（增量消失）。近年特征-收益关系弱化（D 最差月 2024-01 IC −0.373、2026-05 −0.281，微盘剧烈波动期），LGBM 未表现出比基准更强的适应性。

### 4.4 达线判定（预登记执行）

门槛：ΔICIR ≥ +0.15 且五分段无方向翻转。实际：Δ = +0.084（D）/ +0.050（O），翻转条件满足（两配置五分段全正）但**增量未达线 → 不进 E2 预注册，负结果归档**。方向二按 R-249 预案归入"低预期兑现"：月频 IC 口径下非线性组合的残余信息真实存在但量级不足，与 A4D/A9/A4b 三连负 + R-235"边际枯竭"判断一致。

## 五、独立验收（复算记录）

- V1 逐月 score↔IC 复算：2011-01 / 2018-06 / 2025-12 三月 spearman(score_npy, R) 与 csv 逐位一致 ✓
- V2 原始 K 线复算：000001 2020-07 月收益 raw=0.042188 = panel ✓；amt20 raw 与 panel 相对差 1e-9（float32）✓
- V3 walk-forward 边界：代码路径 j∈[m−60,m−1] 实查（train_eval 函数）+ 首月边界展开 ✓
- V4 ranksum 单月独立秩实现复算 2018-06：0.022303 = csv ✓
- 详见 HP:/tmp/r0414_verify.py 输出与 results/work/r0414/lgbm_run.log

## 六、来源清单

| 数字 | 数据文件 | 计算脚本 |
|---|---|---|
| 面板（8特征+R+MASK, md5 738727d3…） | HP:~/quant-evolve/results/work/r0414/panel.npz | HP:~/quant-evolve/results/work/r0414/r0414_panel.py |
| 基准 IC 序列（md5 bf6e8336…） | …/r0414/ranksum4_ic_monthly.csv + ranksum4_summary.json | 同上 |
| LGBM IC 序列 D/O（md5 80610b42…/5a747bf3…）+ 逐月 score（186×2 npy） | …/r0414/lgbm_ic_monthly_{D,O}.csv, lgbm_scores_{D,O}_*.npy | …/r0414/r0414_lgbm.py |
| 五分段/五分位/达线判定（md5 5efbc7a9…） | …/r0414/analysis.json + analysis2.json | …/r0414/r0414_analyze.py |
| 超参/试验计账（20 trial + cfg） | …/r0414/lgbm_summary.json + lgbm_run.log | — |
| fin_deep 数据债实查 | /tmp/r0414_probe*.py 输出（本 notes 转录） | — |
| 面板构建元数据 | …/r0414/panel_meta.json | — |

运行日志：…/r0414/panel_run.log（DONE 92s）、lgbm_run.log（O 组 20 trial + D/O walk-forward ~330s）。未修改 evolution_pipeline.py / registry / paper_engine / crontab；HP 既有进程未动。过程笔记：shared/results/work/task-0414-notes.md。

## 七、结论与建议

1. **负结果归档**：按预登记判定不进 E2。方向二关闭条件与 R-249 §三预案一致——若后续重启，唯一可能有增量的形态是"ML 评分仅作打破平手的软信号"或加入 fin_deep cash-flow 列（需先解决 44.5% 广度覆盖），预期边际均有限。
2. **方法论资产**：本试点建立了可复用的 walk-forward IC 画像管线（panel.npz → lgbm → analysis 三段式、逐月落盘断点续跑、md5 锁定、独立复算四件套），后续任何非线性/组合方式试验可直接套用，试验计账纪律（20 trial 封顶）可防 xhs 帖式贝叶斯过拟合。
3. **对 R-249 地图的影响**：方向二（ML 非线性组合）加入负结果清单，与方向五（SUE）同处置；迭代优先级维持方向一（情绪维度）与择时层 v2 / 风控组件。
