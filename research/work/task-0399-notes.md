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
