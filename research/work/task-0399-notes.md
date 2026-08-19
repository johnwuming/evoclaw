# task-0399 过程笔记（A15 风控组件对照批）

## 目标
在在役 a9_ranksum_raw 血统上验证：C1(n_hold=30) / C2(dd_control) / C3(叠加) / C4(dd阈值敏感性)，评分 v1.1 incumbent=a9_ranksum_raw；另产监控画像 monitor_signals/。

## 时间线
- 14:21 启动。报告编号确认：R-242 为现有最大 → 本批 R-243。

## 待核验点
- [ ] registry a9_ranksum_raw.json 内容（参数 schema）
- [ ] evolution_pipeline.py 的 score_composite 接口与调用方式
- [ ] breadth.parquet 字段
- [ ] 中证2000/沪深300/成交额在库情况
- [ ] 回测脚本调用方式（参考 a13 / task-0394 的跑法）

## 14:25 核验点1：引擎组件可用性
- backtest_dividend_quality_iter.py L294-297: dd_ctl/dd_thresh/dd_reduce/dd_recover 均为引擎原生参数，L536 起为 dd 控制逻辑（满仓且 cur_dd<=-thresh → pos_ratio=dd_reduce；回升至 >= -dd_recover → 恢复满仓）。组合层面回撤控制。
- n_hold 原生参数（在役=20，a13 BASE 默认 30）。
- 结论：C1-C4 全部可参数化实现，不改引擎。调用框架沿用 a13_run.py（a9_common.load_engine/patch_engine/build_timing/write_dual_artifacts）。
- 评分框架沿用 a13_score.py，ACTIVE_ID 改 a9_ranksum_raw，CANDS 换 a15_*。

## registry 关键数字（在役 a9_ranksum_raw）
- locked: ann 21.76% / mdd -33.55% / sharpe 1.3435 / calmar 0.6485
- full: ann 22.16% / mdd -33.55% / sharpe 1.3624 / calmar 0.6605
- gate: icir_is 1.4651 / icir_oos 1.4298 / max_corr 0.6249 / dsr 0.9999
- 因子: circ_mv, avg_amount_20d, pb_inv, roe_ttm, ret120

## 14:36 核验点2：监控画像完成（results/monitor_signals/）
- current.json: breadth 0.4537(2026-08-10), 20d均值0.5402 | size_rel_20d -0.0435(zz500-hs300, 08-07, 中证2000缺库降级) | amt20 23197亿元(全A含退市, 08-10)
- 产物: breadth_monthly.csv / size_rel_monthly.csv / amt20_monthly.csv / current.json, 均短列名无横向滚动
- 解读: 当前市场宽度中性偏弱、中盘显著弱于大盘(-4.35% 20日)、成交额2.3万亿高位

## 状态
- a15_run.py 已启动(PID 276383), 择时构建完成75s, 候选回测进行中
- a15_score.py / a15_dd_segments.py 已上传 compile-ok, 待回测完成后串行运行

## 14:44 核验点3：C1 结果（对照在役 locked 21.76%/-33.55%/1.3435）
- C1 a15_nh30: full 21.50%/-34.54%/1.337 | locked 20.97%/-34.54%/1.314
- 结论苗头: n_hold=30 在 ranksum_raw 血统上三项全劣化（年化-0.8pp, mdd深1pp, sharpe-0.03）——与 a11_nh30(v6a线) 改善 mdd 的结论相反, 血统差异显著
- 剩余: C2(ddc20)/C3(叠加)/C4(ddc15/25), 每 ~5.4min

## 14:55 核验点4：C2 结果
- C2 a15_ddc20: full 19.92%/-27.16%/1.373 | locked 19.25%/-27.16%/1.354
- vs 在役: mdd -33.55→-27.16 (压6.4pp), sharpe 1.3435→1.354 (微升), ann 21.76→19.25 (-2.5pp)
- Calmar: 0.6485→0.708 (+9%)。风险调整后改善, 代价是绝对收益。候选池价值明确。

## 15:06 核验点5：C1-C4 全部完成（1728.5s，预算内）
locked 口径对照（在役 21.76%/-33.55%/1.3435/calmar 0.6485）:
| 候选 | ann | mdd | sharpe | calmar |
| C1 nh30 | 20.97 | -34.54 | 1.314 | 0.607 |
| C2 ddc20 | 19.25 | -27.16 | 1.354 | 0.709 |
| C3 nh30+ddc20 | 18.53 | -27.72 | 1.323 | 0.668 |
| C4a ddc15 | 18.39 | -25.33 | 1.355 | 0.726 |
| C4b ddc25 | 19.87 | -30.20 | 1.374 | 0.658 |
- nh30: 三项全劣化, 与 a11(v6a线) 结论相反 → 血统敏感组件, 判不可行
- ddc 单组件: 回撤压制单调于阈值(0.15>-25.33 / 0.20>-27.16 / 0.25>-30.20), 年化代价 2-3.4pp, sharpe 全部≥在役
- 叠加 C3 比 C2 差 → nh30 无增益, 排除
