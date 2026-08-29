# R-367 — dividend 刷新四件套实装（task-0566，已实施）

- 日期：2026-08-29 ｜ 依据：R-364 评估方案 §5（P0-P3），用户 18:34 批准全部四件
- 结论先行：**四件套全部落地并实测通过。修复后首跑即抓到 8/13 后新公告分红 87 条，其中两只在役持仓（002027 将正常入账 ¥75；300824 因除息日早于已推进水位属晚到事件，见 §4）。ex_date 覆盖上限 2026-08-21 → 2026-09-10。**

---

## 1. 四件套清单与证据

### ① 刷新脚本期内增量（scripts/prep_dividend_roa.py，396→420 行）
- 新增模块级 `_resolve_refresh_set(done_dates, refresh_recent, refresh_periods)`；`fetch_dividend_events` 跳过条件由 `p in done_dates` 改为 `p in done_dates and p not in force_set`
- CLI 新增 `--refresh-recent N`（强制重拉最近 N 个已缓存报告期）与 `--refresh-periods 逗号列表`；**默认参数下行为与旧版完全一致**（force_set 为空）
- 幂等机制沿用既有 `_flush_events`：旧数据先入、重拉行后入，`drop_duplicates([code,ex_date], keep="last")` 新行覆盖旧行
- 单测：`_resolve_refresh_set` 7 例（最近两期/显式/并集/默认空/未知期过滤/空缓存），全过

### ② 引擎前置新鲜度闸（scripts/paper_engine.py，1870→1973 行，**纯新增 103 行、零删除**）
- `_div_parquet_freshness()`：parquet mtime 距今 >7 天，或 max(ex_date) 落后今日 >45 天 → 判过期；读失败按过期处理不抛异常
- `div_freshness_gate(state)`：在 `action_daily()` 中 `load_state` 后**一处调用**（L1433），不阻塞日更、不写 state、不动水位
- 在役实测：刷新前跑出告警 `parquet mtime 距今 16.3 天 > 7 天` 并落盘 alerts 文件；刷新后重跑闸门静默（告警文件仍 1 行，不重复）

### ③ 水位告警（与②同文件，写入 results/paper-div-alerts.csv）
- `_div_coverage_alerts()`：parquet mtime 过期 且 持仓 code 在未来 30 天窗口有已知 ex_date → 逐持仓告警行（语义：窗口内后公告的分红 parquet 抓不到，提醒刷新防静默漏账）
- `_write_div_alerts()`：按 `(alert_date,type,code)` 去重追加；**独立文件**，不动 state/trades/nav/ledger
- 单测 8 例：过期+窗口内触发、新鲜不触发、窗口外不触发、空持仓不触发、去重幂等、gate 端到端不动水位；全过
- 实施说明：②③合并在 paper_engine 同一插入点（一处小改），②为数据级新鲜度、③为持仓级临近除息，均只告警不阻塞——与任务书"账本/日更侧检测+方案自定"一致

### ④ 兜底 cron（HP crontab，41→42 行）
- 新增行：`0 17 * * * cd ~/quant-evolve && flock -n /tmp/prep_div_cron.lock /home/noname/miniconda3/envs/quant/bin/python scripts/prep_dividend_roa.py --only div --refresh-recent 2 >> logs/prep_div.log 2>&1`
- 改前备份 `~/crontab.bak-task0566-20260829`（41 行），改后 `diff` 核对**仅新增本行（41a42），无其它变动**；flock 防重入；17:00 避开 16:30 paper daily / 18:00 qfq 在役窗口；日志落 logs/prep_div.log 静默
- 与 R-364 P3 的差异：按任务书"每日 17:00"取 `* * *` 而非 `1-5`；周末跑一次仅 2 个 akshare 请求，幂等无害

## 2. 刷新前后对比（关键实测）

| 指标 | 刷新前（2026-08-13 快照） | 刷新后（首跑实测） |
|---|---|---|
| parquet 行数 | 48,081 | **48,182（+101）** |
| ex_date 上限 | 2026-08-21 | **2026-09-10** |
| ex_date>8/21 的事件 | 0 | **87 条** |
| 报告期数 | 43 | 43（无丢失） |
| mtime | 08-13 03:30 | 08-29 10:55 |
| 强制重拉 | — | 20251231: 3,621 条 / 20260630: 78 条，失败 0 期 |

- **幂等**：重跑第二次 → 仍 48,182 行零重复；日志 `强制重拉 ['20251231','20260630']` 后正常去重
- **零污染**：paper-state.json mtime 保持 08-29 02:43:10 不变；trades/nav/paper-div-ledger 均未产生；唯一新文件 results/paper-div-alerts.csv（设计交付物）
- **py_compile**：两脚本 HP 上通过
- **单测**：tests/test_task0566.py 新增 19/19 PASS；tests/test_task0546.py 回归 33/33 PASS 无回归

## 3. 实装对在役持仓的直接价值

| 持仓 | 除息日 | 每股分红 | 份额 | 金额 | 判定 |
|---|---|---|---|---|---|
| 002027 | 2026-09-04 | ¥0.05 | 1,500 | **¥75.00** | ex_date>水位 8/28 → 下次 daily 正常入账（旧数据下将永久漏账） |
| 300824 | 2026-08-24 | ¥0.085 | 900 | ¥76.50 | **晚到事件**：ex_date 早于已推进水位 8/28，按现行窗口过滤语义不入账（见 §4） |

## 4. 遗留与建议（不在本任务范围，需用户决策）
1. **300824 晚到事件 ¥76.50**：R-364 §1.3 已指出"晚到事件被窗口过滤永久跳过"是水位语义的已知代价。本次实际发生一例。如需补账，需人工决定：一次性手工调 state 现金+台账，或给 credit_dividends 加"晚到事件补账"逻辑（动在役语义，须单独立项）。
2. freshness 阈值（mtime>7 天 / 覆盖落后>45 天）与告警文件路径为本次定稿默认值，改参数只需调 `_div_parquet_freshness` 默认实参。
3. cron 为每日跑（含周末），若嫌淡季噪声可将 `* * *` 收窄为 `1-5`，一行改动。

## 5. 回退方法
- ①③脚本：HP 上 `cp scripts/prep_dividend_roa.py.bak-task0566-20260829 scripts/prep_dividend_roa.py`；`cp scripts/paper_engine.py.bak-task0566-20260829 scripts/paper_engine.py`（回退后 py_compile 一次）
- ④ cron：`crontab ~/crontab.bak-task0566-20260829`（整体还原到 41 行状态）
- 数据：刷新仅追加/覆盖 (code,ex_date) 同键行，无删除；如需回滚 parquet，可按本报告 §2 前数字 48,081 自行裁剪（一般无必要）
- 告警文件：删 results/paper-div-alerts.csv 即可（引擎会在条件满足时重建）

## 6. 文件清单
- 改：`scripts/prep_dividend_roa.py`、`scripts/paper_engine.py`、HP crontab（+1 行）
- 新：`tests/test_task0566.py`、`results/paper-div-alerts.csv`、`data/derived/dividend_events.parquet`（刷新）
- 备份：`scripts/prep_dividend_roa.py.bak-task0566-20260829`、`scripts/paper_engine.py.bak-task0566-20260829`、`~/crontab.bak-task0566-20260829`
- 未触碰：evolution_pipeline.py、registry、trades.csv schema、paper-state 语义
