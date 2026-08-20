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

## 修复实施（17:15 更新）

### 改动文件（HP ~/quant-evolve）
1. `scripts/paper_trade.py`（改前备份 `scripts/paper_trade.py.bak.20260820`，纯插入 156 行 / 0 删除，4 个块）：
   - L163-291 新增：`_bj_now()`（HP=UTC，收盘/当日判断显式 UTC+8）、`_tencent_closes()`（腾讯批量快照兜底，仅接受当日时间戳）、`fetch_pit_closes(codes)`（东财 akshare 全市场→腾讯兜底，/tmp/task0368_spot_日期.csv 同日缓存）、`apply_pit_price_override()`（≥15:05 北京时间才启用；单票偏离>35% 疑似除权回退旧价并留痕）
   - L679-702 `action_rebalance` 在卖出前插入 PIT 覆盖块：目标池∪持仓的 price_dict 全部替换为当日官方收盘；latest_date 同步改为调仓当日（与回测 rebalance_dates=groupby(M).min() 的 d 对齐）；state 新增 `pit_price` 审计块（price_date/codes_fresh/codes_fallback/parquet_last_date；整体失败时记录 lag_days_cal 量化滞后）
   - L727/L808 卖出/买入 trade 行新增 `price_date` 列（逐票标注取价日期，供 task-0400 防漂移抽查）
2. `scripts/task0368_dryrun.py`（新增，只读干跑校验）
3. `logs/task0368_dryrun.log`（验证日志）
4. 未动：paper_engine.py（含 guard_override_and_drift 防漂移比对）、registry、evolution_pipeline.py、crontab、action_daily/action_init

### diff 摘要
162a163,291 / 549a679,702 / 573a727 / 653a808 —— 全部为 append，无删改旧行。

### 环境事实（新发现）
- HP 时区=UTC：北京时间判断必须显式 +8，否则 16:30 CST(=08:30 UTC) 的收盘守卫永不触发（初版 bug，干跑抓出后已修）
- akshare 东财 push2 在 HP 上经 requests 持续 Connection aborted（curl 可通，疑 UA/会话被拒）→ 腾讯 qt.gtimg.cn 批量接口稳定可用，作兜底源

### 干跑验证结果（2026-08-20 17:11 北京时间，logs/task0368_dryrun.log）
- 抽样 11 只（8 持仓 + 000001/000002/600519）
- 修复前（parquet 尾行）：全部 2026-08-19 收盘价 → 若今日为月首调仓日，将滞后 1 个交易日
- 修复后：11/11 只取到 2026-08-20 当日收盘（如 000001 11.270→11.400、300009 8.460→10.150 即 20cm 涨停价、600519 1307.88→1291.50）
- 交叉验证：3/3 与腾讯 qfq 日线当日 bar 收盘完全一致（11.4/3.14/8.43）→ 快照价=当日官方收盘
- 机制路径 `apply_pit_price_override` 实际走通（ASSERT OK：price_dict 被当日收盘覆盖）；未到收盘(<15:05)时保守回退逻辑亦验证生效
- `python -m py_compile scripts/paper_trade.py scripts/task0368_dryrun.py` 通过

### 与回测口径等价性论证
- 回测（backtest_dividend_quality.py）：调仓日 d=groupby(M).min()（月首交易日），成交价=closes[d]（d 当日收盘）
- 修复后 paper：gate 判定月首交易日 → 16:30 CST 调仓 → 覆盖价为 d 当日官方收盘（东财/腾讯收盘后快照，腾讯 K 线交叉验证一致）→ 与 closes[d] 同一价格、同一日期 → **滞后归零**
- 数据频率限制说明：选股因子仍用 parquet（截至 t-1 收盘后 18:00 日更），与"价格"缺陷无关，属既有口径；价格本身不再受周更/日更时点影响
- 延迟核验建议：9/2 晨核对 task-0402（baostock 18:00 日更）落盘的 9/1 parquet 收盘 == 9/1 调仓日志中的覆盖价（跨源一致性闭环）

### 回滚方式
`cp scripts/paper_trade.py.bak.20260820 scripts/paper_trade.py`（字节级还原；新 state 字段 pit_price 与 trades 新列 price_date 对旧代码无害，旧代码读取时忽略/置 NaN）
