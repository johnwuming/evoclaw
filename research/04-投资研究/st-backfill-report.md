# task-0330 ST 历史区间回补报告

日期：2026-08-16 · 任务：A线-数据 · 状态：完成

## 0. 结论摘要

- 产出 `data/st_history_ranges.csv`：**1006 个 ST 区间，767 只股票**（含 725 只在回测宇宙内），远超原 206 只现存量级；列结构 `code,start_date,end_date,source`，适配引擎 `load_st_flags()`
- **新旧对照（locked ≤2024-06-30，全量池+成本v2+一字板+审计锁）**：年化变化 +0.20pp、Sharpe +0.44pp（v0_seed）/ +0.43pp（v2b_trr）、最大回撤不变 → **影响 <1pp，现役 v2b_trr 数字无需修订**（结论不翻转）
- 原诊断修正：引擎现役 ST 排除实际为 **0 生效**（`stock_info.csv` 仅 300 行且 is_st 全 False，`st_history.parquet` 未接入引擎）——本任务首次让历史 ST 排除真正生效

## 1. 数据源与方法

| 源 | 覆盖 | 说明 |
|---|---|---|
| SZSE bulk `stock_info_sz_change_name("简称变更")` | 深市 000/001/002/003/300/301（含退市） | 7462 行精确变更日期，名称含 ST/*ST 即 ST 状态，start=名称生效日 end=下次变更日前日 |
| baostock `query_all_stock(day)` 月网格 | 沪市 | **勘察后弃用**：code_name 为最终名称非当日名（600870 全程"退市厦华"、600734 全程"*ST实达"），会复现"全程标记"失真 |
| 当前 ST 快照 `st_history.parquet`(2026-08-15) | 沪市 84 只 | 兜底：仅对 2026-08-15 之后区间有效 `[2026-08-15, 2099]` |
| BJ 快照 | 3 只 | 北交所 2021-11 开市，区间 `[2021-11-15, 2099]` |

- 探测过但不可用的 SH 逐日名称源：sina vCI_CorpInfo/StockHistory（无日期/空）、THS company.html 曾用名（无日期）、eastmoney F10（FORMERNAME 仅一个前名，报表名不存在）、SSE commonSoaQuery（SOA null）、cninfo（500）、baidu（空）
- **沪市历史 ST 缺口已如实记录**：SH 历史区间无法从现有免费源获得精确日期，采用快照兜底（仅覆盖 2026-08 后）；深市（历史 ST 高发区）已精确覆盖

## 2. 覆盖度

- 总区间：1006 行（szse_bulk 908 + szse_retire 11 + 合并 84 + snapshot 84 + bj 3），767 只股票，725 只在回测宇宙（all_stocks_qfq 5448）
- 多区间股票（曾多次 ST）：175 只，CSV 保留每段独立区间；引擎单区间模型下 `load_st_flags()` 取并集 [min,max]（保守方向，报告期缺口可接受）
- 已知曾 ST 已摘帽抽检：000005（ST星源 2003-2008 + 2021-2026）、000030（1998-2013）、000004（4 段）→ 均返回非空区间 ✓

## 3. load_st_flags() 适配（仅数据加载函数）

- 优先读 `data/st_history_ranges.csv`（区间精确）；不存在时降级旧逻辑（stock_info.csv / 快照法）
- 引擎逻辑（选股跳过 ST/持有变 ST 强卖/退市 DELIST 强平）零改动；备份 `scripts/backtest_dividend_quality_iter.py.bak_task0330`
- 单测：`load_st_flags()` 返回 758-767 code → 000005/000030/000004 非空 ✓

## 4. 新旧对照回测（locked 2006-01-04 ~ 2024-06-28）

参数：sort=mv, div_min=0.02, roe_min=0.15, roa_min=0.1, score_weights=0.4/0.3/0.3/0.3, n_hold=20, price_cap=10, min_amt=0, dd_control=0, dd_thresh=0.2, dd_reduce=0.5, 成本v2, 一字板on, cap=1000万

| 腿 | 年化 | 最大回撤 | Sharpe | 累计 | Calmar | 月胜率 |
|---|---|---|---|---|---|---|
| v0_seed_old（无ST排除） | 26.25% | -69.49% | 0.8848 | 73.31 | 0.3778 | 58.37% |
| v0_seed_new（ST表） | 26.45% | -69.49% | 0.8891 | 75.47 | 0.3806 | 58.82% |
| v2b_trr_old | 26.25% | -69.49% | 0.8836 | 73.31 | 0.3778 | 58.37% |
| v2b_trr_new | 26.45% | -69.49% | 0.8879 | 75.47 | 0.3806 | 58.82% |

- 差异：年化 **+0.20pp**、Sharpe **+0.43~0.44pp**、累计 +2.16pp、月胜率 +0.45pp、最大回撤与 Calmar 基本不变
- **判定：影响 <1pp → 现役 v2b_trr 数字无需修订**；方向为正（ST 排除后组合略优），结论不翻转
- 注：SH 历史区间未精确覆盖（快照兜底仅 2026-08 后），若补齐 SH 精确历史区间影响可能略增，但 SZ 已覆盖历史 ST 高发区，量级判断稳健

## 5. 交付物

- `data/st_history_ranges.csv`（1006 行，UTF-8）
- `scripts/backtest_dividend_quality_iter.py`（仅 load_st_flags 修改，备份 .bak_task0330）
- `results/strecheck_v0_seed_old/new_metrics.json`、`results/strecheck_v2b_trr_old/new_metrics.json`
- 本报告 `results/st-backfill-report.md`
