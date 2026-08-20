# task-0368 paper_engine PIT 价格滞后修复笔记

启动：2026-08-20 17:02 GMT+8。目标：paper 月首调仓价与回测 PIT 口径一致（滞后归零）。


## 定位结论（17:10 更新）

### 现状架构（实测确认）
- 月度调仓活跃路径：crontab 16:30（工作日）→ `scripts/cron_paper_rebalance.sh` → `rebalance_gate.py`（官方日历判断月首交易日，task-0347 修复了"调仓日对齐"）→ `scripts/paper_trade.py --action rebalance`
- paper_engine.py 的 rebalance 在 crontab 已注释暂停（#PAUSED-20260816-seedB）；paper_engine daily 16:30 仍活跃，两引擎共享 results/paper-state.json
- 防漂移比对：paper_engine.py 有 guard_override_and_drift（main.json↔registry active 签名比对），evolution_pipeline.drift_signature 与其同口径 —— 不动它

### 回测 PIT 口径（backtest_dividend_quality.py L193/L255 实读）
- rebalance_dates = 交易日 groupby(M).min()（每月首个交易日 d）
- 成交价 = `closes[code].get(d)` —— **调仓日 d 当天收盘价**（"收盘后确定新目标池并执行换仓"）

### paper_trade.py 现状取价（缺陷所在）
- `load_all_latest_data()` 取每只股票 parquet 的**最后一行**（df.iloc[-1]）作为调仓价
- 数据时间线（crontab 实测）：qfq 日更 task-0402 在 **18:00** 跑（16:30 paper 之后）；周全量 refresh_data.py 周日 20:00
- 因此月首交易日（如周一 9/1）16:30 调仓时，parquet 最后一行是**上周五 8/29 收盘** → 调仓价滞后 1 个交易日（日历 3 天）；若日更失败/未覆盖则滞后更长（历史实例：8/13-8/14 时 parquet 只到 8/7，滞后整周，paper_engine 老口径因 get_latest_trade_date=8/7 永久 skip）
- gate 修复后调仓日对了，但价格仍取 parquet 尾行 = R-226 所述缺陷，确认属实

### 修复方案（零滞后，不动 crontab）
- 在 paper_trade.py `action_rebalance` 增加"当日收盘价在线补拉"：调仓时(≥15:00 收盘后)用 akshare `stock_zh_a_spot_em`（东财全市场快照，收盘后=当日官方收盘价）对目标池+持仓取当日收盘价，覆盖 parquet 尾行价
- 失败兜底：回退 parquet 尾行旧口径并在日志+state 量化滞后天数（parquet 末日 vs 今日），不默默用旧价
- qfq 口径说明：parquet 为 qfq-锚定尾行（尾行=该日原始价），当日原始收盘=当日锚定 qfq 价，与回测 closes[d] 同义；除权导致的持仓 PnL 口径问题为引擎既有特性，不在本任务范围
