# R-391 gold 引擎「月末 NaN→w=0」缺陷审计与修复方案

- **任务号**：task-0606（P1 审计；只读+方案，**未实施任何修复**）
- **日期**：2026-08-31 晚（HP 只读实查 + 本地账本对账 + 反事实重算）
- **编号说明**：目标号 R-390 在本报告写作期间被并行任务占用（`R-390-月末日频口径错配低估系数与DDC阈值核实.md`），按取号规则顺延为 **R-391**。

## 1. 背景与已核实事实

**缺陷机制**（`~/quant-evolve/scripts/paper_engine_gold.py` L85-92，HP 只读确认）：

```python
m = s.resample("ME").last().dropna()                # px 取月内最后交易日收盘（asof 语义，正确）
sma200 = s.rolling(200).mean().reindex(m.index)     # 缺陷：按日历月末精确匹配 → 月末逢非交易日 = NaN
vol60  = s.pct_change().dropna().rolling(60).std().reindex(m.index) * np.sqrt(252)   # 同缺陷
dir200 = (m.values > sma200.values)                 # NaN 比较 = False → 0
vt10 = (0.10/vol60).clip(0,1); w_sig = (dir200*vt10).fillna(0.0)   # → w 强制 0
```

日历月末逢周六/日/节假日时：该日无行情行 → `reindex` 得 NaN → `dir200=False` 且 `vt10=NaN` → **w_sig 被强制归 0**，而非取月末前最后交易日的真实信号。

**污染链**（本次实查新增证据）：

1. 引擎本体 `paper_engine_gold.py`（每日 07:40 工作日 cron 跑 daily）；
2. **影子账本生产者 `engines_shadow_nav_gold.py` L76-84 携带逐行相同的缺陷**（`w = w_sig.shift(1)`，每月 3 日 09:38 cron append）；
3. **评估器 `engines_shadow_evaluate_gold.py` 消费 shadow_nav.csv** 计算 ann/MDD/Calmar/rolling12_ann（每月 3 日 09:40 cron）。

**对账验证**：用引擎同源数据（腾讯 fqkline sh518880 qfq 日频，daily_rows=3183，2013-07-29~2026-08-28）独立重算 158 个月末的 w，与本地账本 `shadow_nav.csv`（157 行）w_applied **157/157 全对账一致**（差异 <5e-5，为账本 4 位小数舍入）→ 账本确实记录的是缺陷语义的 w。成本模型同样逐行验证通过（net = gross − 0.0013×|Δw|，157/157）。

**时点状态**：2026-08-31（周日）月末：px=9.4750，sma200_asof=9.4941 → 真实 w=0，引擎 w=0——**结果碰巧一致，机制已坏**（下月信号不受本次缺陷影响）。

## 2. NaN 月全清单（61/158 个月末）

- **热身期 NaN：10 个月**（2013-07~2014-04，上市不足 200 交易日，asof 语义下同样无值 → w=0 属正当行为）；
- **纯日历 NaN：51 个月**（月末逢非交易日；asof 语义下有真值）；
- 51 个日历 NaN 月末中：**33 个月末 w 被错误归 0 且真值 ≠0**（污染源），**18 个月末两侧碰巧同为 0**（结果侥幸一致，机制仍错）。

表1：全部 61 个 NaN 月末对照（w_eng 恒为 0；w_true 为 asof 语义真值）

| 月末 | px | sma200_asof | w_eng | w_true | 类型 | w分歧 |
|---|---|---|---|---|---|---|
| <bound method Timestamp.date of Timestamp('2013-07-31 00:00:00')> | 2.6570 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2013-08-31 00:00:00')> | 2.7870 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2013-09-30 00:00:00')> | 2.6490 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2013-10-31 00:00:00')> | 2.6130 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2013-11-30 00:00:00')> | 2.4430 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2013-12-31 00:00:00')> | 2.3760 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2014-01-31 00:00:00')> | 2.4610 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2014-02-28 00:00:00')> | 2.6210 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2014-03-31 00:00:00')> | 2.5730 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2014-04-30 00:00:00')> | 2.6120 | NaN(不足200日) | 0.0000 | 0.0000 | 热身 | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2014-05-31 00:00:00')> | 2.5350 | 2.5699 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2014-08-31 00:00:00')> | 2.5540 | 2.5490 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2014-11-30 00:00:00')> | 2.3530 | 2.5386 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2015-01-31 00:00:00')> | 2.5420 | 2.5058 | 0.0000 | 0.5790 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2015-02-28 00:00:00')> | 2.4650 | 2.4997 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2015-05-31 00:00:00')> | 2.3810 | 2.4379 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2015-10-31 00:00:00')> | 2.3510 | 2.3784 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2016-01-31 00:00:00')> | 2.3630 | 2.3155 | 0.0000 | 0.8010 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2016-04-30 00:00:00')> | 2.6600 | 2.3716 | 0.0000 | 0.6151 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2016-07-31 00:00:00')> | 2.8590 | 2.5135 | 0.0000 | 0.5807 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2016-12-31 00:00:00')> | 2.6360 | 2.7269 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2017-01-31 00:00:00')> | 2.6410 | 2.7344 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2017-04-30 00:00:00')> | 2.8120 | 2.7674 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2017-09-30 00:00:00')> | 2.7420 | 2.7357 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2017-12-31 00:00:00')> | 2.7080 | 2.7450 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2018-03-31 00:00:00')> | 2.6920 | 2.7267 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2018-04-30 00:00:00')> | 2.6920 | 2.7235 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2018-06-30 00:00:00')> | 2.6610 | 2.7110 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2018-09-30 00:00:00')> | 2.6230 | 2.6836 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2018-12-31 00:00:00')> | 2.8260 | 2.6896 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2019-03-31 00:00:00')> | 2.7880 | 2.7283 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2019-06-30 00:00:00')> | 3.1090 | 2.7937 | 0.0000 | 0.8822 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2019-08-31 00:00:00')> | 3.5080 | 2.9229 | 0.0000 | 0.4932 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2019-11-30 00:00:00')> | 3.2650 | 3.0988 | 0.0000 | 0.7956 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2020-01-31 00:00:00')> | 3.4300 | 3.1991 | 0.0000 | 0.7025 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2020-02-29 00:00:00')> | 3.6230 | 3.2754 | 0.0000 | 0.6183 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2020-05-31 00:00:00')> | 3.8640 | 3.4774 | 0.0000 | 0.4229 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2020-10-31 00:00:00')> | 3.8970 | 3.8075 | 0.0000 | 0.4945 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2021-01-31 00:00:00')> | 3.7780 | 3.9076 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2021-02-28 00:00:00')> | 3.6130 | 3.9082 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2021-07-31 00:00:00')> | 3.7200 | 3.7416 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2021-10-31 00:00:00')> | 3.6090 | 3.6744 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2022-01-31 00:00:00')> | 3.5940 | 3.6572 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |
| <bound method Timestamp.date of Timestamp('2022-04-30 00:00:00')> | 3.9420 | 3.6977 | 0.0000 | 0.6023 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2022-07-31 00:00:00')> | 3.7490 | 3.7432 | 0.0000 | 0.8882 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2022-12-31 00:00:00')> | 3.9860 | 3.8383 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2023-04-30 00:00:00')> | 4.2980 | 3.9398 | 0.0000 | 0.8140 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2023-09-30 00:00:00')> | 4.4360 | 4.2656 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2023-12-31 00:00:00')> | 4.6480 | 4.4315 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2024-03-31 00:00:00')> | 5.1260 | 4.5588 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2024-06-30 00:00:00')> | 5.2970 | 4.8357 | 0.0000 | 0.5511 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2024-08-31 00:00:00')> | 5.5220 | 5.0401 | 0.0000 | 0.6964 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2024-11-30 00:00:00')> | 5.9230 | 5.3885 | 0.0000 | 0.7014 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2025-01-31 00:00:00')> | 6.2020 | 5.6302 | 0.0000 | 0.7716 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2025-05-31 00:00:00')> | 7.3690 | 6.2754 | 0.0000 | 0.4316 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2025-08-31 00:00:00')> | 7.4860 | 6.8388 | 0.0000 | 1.0000 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2025-11-30 00:00:00')> | 9.0670 | 7.6062 | 0.0000 | 0.4056 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2026-01-31 00:00:00')> | 11.0090 | 8.2630 | 0.0000 | 0.3687 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2026-02-28 00:00:00')> | 10.9330 | 8.4841 | 0.0000 | 0.2638 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2026-05-31 00:00:00')> | 9.3970 | 9.2673 | 0.0000 | 0.3171 | 日历NaN | 是 |
| <bound method Timestamp.date of Timestamp('2026-08-31 00:00:00')> | 9.4750 | 9.4941 | 0.0000 | 0.0000 | 日历NaN | 否(两侧同0) |

## 3. 污染评估（对 gold 影子账本）

**33 个被污染的账本行**（账本行 M 的 w 来自上月末信号；上月末为日历 NaN 且 w_true≠0）：

表2：污染月明细（w_applied 全为 0；毛收益差 = (w_true−w_applied)×gold_ret，正=少赚）

| 账本行月份 | w_applied | w_true | 当月 gold_ret | 毛收益差 | 性质 |
|---|---|---|---|---|---|
| <bound method Timestamp.date of Timestamp('2014-09-30 00:00:00')> | 0.0000 | 1.0000 | -4.89% | -4.89pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2015-02-28 00:00:00')> | 0.0000 | 0.5790 | -3.03% | -1.75pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2016-02-29 00:00:00')> | 0.0000 | 0.8010 | +9.48% | +7.59pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2016-05-31 00:00:00')> | 0.0000 | 0.6151 | -3.16% | -1.94pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2016-08-31 00:00:00')> | 0.0000 | 0.5807 | -1.26% | -0.73pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2017-05-31 00:00:00')> | 0.0000 | 1.0000 | -1.32% | -1.32pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2017-10-31 00:00:00')> | 0.0000 | 1.0000 | -0.88% | -0.88pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2019-01-31 00:00:00')> | 0.0000 | 1.0000 | +0.39% | +0.39pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2019-04-30 00:00:00')> | 0.0000 | 1.0000 | -0.39% | -0.39pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2019-07-31 00:00:00')> | 0.0000 | 0.8822 | +1.77% | +1.56pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2019-09-30 00:00:00')> | 0.0000 | 0.4932 | -3.19% | -1.57pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2019-12-31 00:00:00')> | 0.0000 | 0.7956 | +3.64% | +2.90pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2020-02-29 00:00:00')> | 0.0000 | 0.7025 | +5.63% | +3.95pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2020-03-31 00:00:00')> | 0.0000 | 0.6183 | -1.02% | -0.63pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2020-06-30 00:00:00')> | 0.0000 | 0.4229 | +1.29% | +0.55pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2020-11-30 00:00:00')> | 0.0000 | 0.4945 | -6.90% | -3.41pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2022-05-31 00:00:00')> | 0.0000 | 0.6023 | -1.65% | -0.99pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2022-08-31 00:00:00')> | 0.0000 | 0.8882 | +0.24% | +0.21pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2023-01-31 00:00:00')> | 0.0000 | 1.0000 | +2.08% | +2.08pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2023-05-31 00:00:00')> | 0.0000 | 0.8140 | +1.56% | +1.27pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2023-10-31 00:00:00')> | 0.0000 | 1.0000 | +4.15% | +4.15pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2024-01-31 00:00:00')> | 0.0000 | 1.0000 | +0.11% | +0.11pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2024-04-30 00:00:00')> | 0.0000 | 1.0000 | +3.12% | +3.12pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2024-07-31 00:00:00')> | 0.0000 | 0.5511 | +2.62% | +1.45pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2024-09-30 00:00:00')> | 0.0000 | 0.6964 | +3.35% | +2.33pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2024-12-31 00:00:00')> | 0.0000 | 0.7014 | +0.08% | +0.06pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2025-02-28 00:00:00')> | 0.0000 | 0.7716 | +3.90% | +3.01pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2025-06-30 00:00:00')> | 0.0000 | 0.4316 | -0.75% | -0.32pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2025-09-30 00:00:00')> | 0.0000 | 1.0000 | +11.39% | +11.39pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2025-12-31 00:00:00')> | 0.0000 | 0.4056 | +2.58% | +1.05pp | 错过涨幅 |
| <bound method Timestamp.date of Timestamp('2026-02-28 00:00:00')> | 0.0000 | 0.3687 | -0.69% | -0.25pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2026-03-31 00:00:00')> | 0.0000 | 0.2638 | -11.29% | -2.98pp | 侥幸避跌 |
| <bound method Timestamp.date of Timestamp('2026-06-30 00:00:00')> | 0.0000 | 0.3171 | -10.84% | -3.44pp | 侥幸避跌 |

**方向统计**：18 个月错过涨幅（最大 2025-09 少赚 +11.40pp）、15 个月侥幸避跌（最大 2014-09 避损 −4.89pp）；**逐月毛收益差合计 +21.66pp**（净方向：缺陷系统性压低了引擎收益）。

**反事实净值**（w_true 全路径替换，同一成本模型，157 个月）：

| 指标 | 实际账本（缺陷语义） | 反事实（asof 真值） | 差异 |
|---|---|---|---|
| 终点净值 | 2.6046 | 3.1707 | **+0.5661（真值高 21.7%）** |
| 年化收益 | 7.59% | 9.22% | **+1.63pp** |
| 最大回撤 | 5.90%（2017-06-30） | 8.09%（2017-10-31） | **深 2.19pp** |

结论：缺陷让 gold 引擎影子账本**年化少算约 1.6pp、终点少 21.7%，同时把 MDD 美化了 2.2pp**——收益与风险画像双双失真，不是中性噪声。2026 年内污染 3 个月：2026-02（w_true=0.369，少亏 0.26pp）、2026-03（w_true=0.264，躲过 2.98pp 跌幅）、**2026-06（w_true=0.317，躲过 3.44pp 跌幅）**；另 2026-01-31（周六）NaN 未造成分歧（两侧同 0）。

## 4. 上游影响确认（谁在消费这条污染链）

| 消费链 | 数据源 | 是否受污染 | 依据 |
|---|---|---|---|
| **展示口径 42% gold 腿（R-380 管道）** | nav_curves.csv gold 列 = shadow_nav.csv nav 列 | **是** | R-389 L22 已证两列逐位一致（1.003798/2.603158）；本报告 L1 证实 nav 列由缺陷 w 生成 |
| **引擎评估/gate 观察（R-305/306 线）** | engines_shadow_evaluate_gold.py 读 shadow_nav.csv | **是** | 月度 ann/MDD/Calmar/rolling12 全部在污染曲线上计算；gold_trend_sma200 已于 2026-08-25 shadow→active（影子期豁免），评估历史含污染 |
| R-372 一线 / R-386「压降42%」对照基线 | gold_ret 裸 B&H | **否** | 裸收益序列不经过 compute_signals（R-389 §2/§4 已证），本次复核确认该陈述成立 |

**展示口径二阶量化**（静态 58/42 月再平衡、不含成本近似；该近似复现 R-380 官方 MDD −9.67% 至 −9.66%，残差 0.01pp，方法可信）：

| 指标 | 展示口径（实际） | 反事实（asof 真值金腿） |
|---|---|---|
| 组合终点（156 月） | 5.80 | 6.32（+9.0%） |
| 组合年化 | 14.48% | 15.24%（+0.76pp） |
| 组合 MDD | 9.66%（2015-08-31） | 9.66%（2015-08-31，持平——最深回撤由 A 腿 2015 股灾主导） |

**须更正的既有陈述**：R-389 L50「gold 引擎当月 w_applied=0（信号空仓持货基），月收益 +0.04%，接住了组合」——机制归因错误。2026-06 行 w=0 来自 2026-05-31（周日）**NaN 强制归零**；真实信号 w_true=0.317（应持约 32% 黄金、当月约 −3.4%）。展示口径 6 月的「抗跌」是缺陷侥幸，不是趋势信号判断。

## 5. 修复方案对比与推荐（只出方案，未实施）

**代码修复本体（A/B 共用）**：两处逐行同构文件（`paper_engine_gold.py`、`engines_shadow_nav_gold.py`）同步改为 asof 语义：

```python
sma200 = s.rolling(SMA_N).mean().reindex(m.index, method="ffill")
vol60  = s.pct_change().dropna().rolling(VOL_N).std().reindex(m.index, method="ffill") * np.sqrt(252)
```

即：日历月末无交易时取此前最后交易日的 SMA200/vol60（与 px 已有的 resample-last 语义对齐）；热身期（<200 日）仍 NaN → w=0，早期行为不变。

**方案 A：修复语义 + 处置历史账本**
- **A1 追加更正事件**：shadow_nav.csv 历史行不动，追加更正说明事件文件，自修复月起新语义入账。
  - 利：不动历史产物、审计痕迹清晰、改动面小。
  - 弊：33 个月污染路径永久固化在曲线里；展示口径与评估指标持续失真；更正事件与曲线分离、读者易漏。
- **A2 重算重发布**：用修复后语义一键重放全历史 shadow_nav（确定性脚本）；旧文件版本化存档（如 shadow_nav_preR391.csv）；同步刷新 nav_curves.csv 展示数据与 evaluate 历史；README 与后续报告标注 R-391 更正。
  - 利：账本/展示/评估三链一次对齐真值；消除跨语义混接。
  - 弊：动生产数据文件（nav_curves 是 BFF 展示源，需下游同步）；R-377/R-380/R-386/R-388/R-389 等已发布引用数字会出现新旧版本分歧，需逐一标注。

**方案 B：仅修未来，不动历史**：只改两处 compute_signals，账本与下游全部不碰。
- 利：改动面最小、零下游同步成本。
- 弊：失真固化同 A1；且引擎已 active，2026-09-03 append 起账本前段污染+后段干净**语义混接**，evaluate 的 rolling12 等滚动指标跨语义不可比。

**推荐：A2**。理由：账本尚未承载真金（paper 影子阶段），重算成本处于最低点；引擎 2026-08-25 已激活，每晚一个月多污染一个月、下游引用越积越多。若用户偏好最小动作可退选 B，但须接受评估与展示口径长期失真及语义混接。无论 A/B，修复后应重跑本报告的复算脚本验证 33 个分歧月末归零。

**⚠️ 实施需用户批准**：本报告仅为审计结论与方案对比。任何代码、账本、展示数据、registry/crontab 的变更均未执行，且未经用户批准不得自动执行。

**若批准 A2 的实施纪律建议**：先 tar 备份 `results/engines/gold/` 全目录；重算先在 /tmp 演跑并 diff 校验（预期仅 33 行 w 与 net/nav 链变化）；nav_curves.csv 走 BFF 原构建管线刷新而非手改；后续以独立报告复核 R-380/R-386/R-388/R-389 引用数字的新旧版本对照。

## 6. 来源清单

**HP 只读（10.12.192.174，未改任何文件）**：
- `~/quant-evolve/scripts/paper_engine_gold.py`（compute_signals L85-92、fetch_gold_daily L58-84、常量 L40-46）
- `~/quant-evolve/scripts/engines_shadow_nav_gold.py`（L76-84 同缺陷、L90 w=shift(1)、L95 成本）
- `~/quant-evolve/scripts/engines_shadow_evaluate_gold.py`（L5-7 读 shadow_nav、L58-64 指标、L95）
- HP crontab（daily 工作日 07:40；verify 周日 03:00；append/evaluate 每月 3 日 09:38/09:40）

**本地产物**：
- `shared/results/04-投资研究/engines/gold/shadow_nav.csv`（157 行账本，w_applied/gold_ret/nav）
- `shared/results/05-量化投资/R-380-vC-0双口径缺口归因拆分.md`、`R-389-两腿基线694pp分歧溯源与insufficient_obs条款.md`（消费链证据）
- `tools/quant-bff/live/data/nav_curves.csv`（156 月展示口径，只读）

**复算脚本与中间数（可重算，均在 `shared/results/work/`）**：
`task-0606-hp-recompute.py`（HP 复算脚本）、`task-0606-hp-signals.csv`（158 月末全量信号）、`task-0606-hp-summary.txt`（NaN/分歧清单）、`task-0606-analyze.py`（对账+反事实）、`task-0606-ledger-join.csv`、`task-0606-contaminated.csv`、`task-0606-nav-true.csv`（反事实净值）、`task-0606-display-impact.json`（展示口径二阶影响）、`task-0606-results.json`（汇总）、`task-0606-notes.md`（过程笔记）。
