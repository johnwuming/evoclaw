# task-0343 过程笔记 2026-08-17 13:10:00

## 阶段1 数据源勘察（13:10-13:15）
- QUANT_REPORTS_DIR=/root/.openclaw/workspace-quant/results（347文件，locked/full metrics+nav+yearly+holdings+trades 全在）
- versions-manifest.json 58KB：dict{generated_at, active=v5h_xsub, versions[56]}，每条含 version_id/strategy_prefix/status/strategy/registered_at/windows{full,locked各含annual_return,max_drawdown,sharpe,calmar,cumulative_return,monthly_win_rate,period_start/end,years,num_rebalance}/files_note
- registry VPS侧已同步：/root/.openclaw/workspace-quant/model/registry/*.json（v5h_xsub.json 3KB，13:02 刚同步，新鲜）
  - 结构：version_id/status/created_at/main_alias/selection{strategy,params{sort,ext_factor,ext_weights,e1_guard,mom_cols,xsub_days},factors[]}/timing{enabled,type,params{layer,q_key,trend,combine},description,signal,data_source}/data_snapshot/code_ref/backtest_refs{endtoend,baseline,metrics{含avg_holdings,monthly_turnover_est},metrics_full}/gate/provenance/activated_at
- decision-log.jsonl 36KB 已同步（model/decision-log.jsonl），每行 ts/decision_id/type/version/trigger/metrics/expected_impact/rollback_condition
- a7_v5h_xsub_formal_locked_metrics.json 字段：annual_return .1574/max_drawdown -.298/sharpe .9983/calmar .5283/monthly_win_rate .6109/monthly_turnover_est .3197/avg_holdings 19.53 + 参数字段(div_min .02/roe_min .15/roa_min .1/price_cap 10/n_hold 20/sort ext/cost_model v2/limit_board on)
- **pos_ratio.csv 不存在**（VPS+HP 都没有）；timing 仓位需合成 = q3z×trend_f
- HP 数据源（ssh -p 2222 noname@10.12.192.174, python=/home/noname/miniconda3/envs/quant/bin/python）：
  - results/timing_signals_iter4.csv：248行月度 2006-01~2026-08，f_q_q3z∈[0.6,1.0]
  - results/a2cx_ew_trend_signal.csv：260行月度 2005-01~2026-08，ew_idx+ma200+trend_f∈{0.6,1.0}
  - data/hs300_daily_20060101_20260808.parquet：5003行日线 date/open/high/low/close/volume，2006-01-04起
- 同步链路（scripts/auto_sync_notify.py）：
  - do_rsync: HP results/→shared/results/04-投资研究/（几乎全量，只排除 EXCLUDES）
  - mirror_quant_results: HP results/→workspace-quant/results/（MIRROR_INCLUDES 白名单：seedB_*,q4b*,*_full/locked_metrics.json,*_full/locked_nav.csv,*_full/locked_yearly.csv,versions-manifest.json）
  - Step1.5/push_now: model/(registry/,main.json,decision-log.jsonl)+manifest+ledger→workspace-quant/（已覆盖 registry/decision-log/ledger ✓ 无需补）
  - **需补**：新基准/仓位文件加 --include=dash_*.csv 进 MIRROR_INCLUDES
- 结论：基准数据齐全（hs300 parquet + ew_idx csv），在 HP 一次性生成 dash_pos_ratio.csv + dash_bench_monthly.csv 落盘 results/，改 sync include 即全自动
