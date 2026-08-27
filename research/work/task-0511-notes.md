# task-0511 R-333 paper真实成本对账审计 — 过程笔记

开始时间：2026-08-27 18:15 GMT+8
约束：全程只读（paper 产物零写）；禁 SSH HP；报告/notes/README日志/completions 为唯一允许写入。

## 0. 镜像盘点（步骤1）

目录：shared/results/04-投资研究/

| 文件 | bytes | lines | mtime |
|---|---|---|---|
| paper-state.json | 1128 | 53 | ? |
| paper-trades.csv | 836 | 11 | ? |
| paper-nav.csv | 329 | 8 | ? |
| paper-portfolio.json | 4792 | 193 | ? |
| paper-summary.json | 1307 | 67 | ? |
| timing_layer_audit.jsonl | 246 | 1 | ? |

另有 engines/gold/paper_state.json、engines/a2/、bak-task0486-20260825 快照待查。

## 关键事实（已核验，步骤1完成）

### A. 两套 paper 状态并存
- paper-portfolio.json（mtime 08-12 02:53）：v1 组合，launch 2026-08-10，10 只全仓（total_invested 99141，cash 859，weight 0.9914）。**此后未更新**。
- paper-state.json（mtime 08-27 00:30）：现行 v2 状态，created 08-17T16:09:39，model=a13_rsraw_e1f10dz，last_rebalance=2026-08-14，8 只持仓 cost 合计 59567 元（100000 本金 ×59.57%），cash=40393，timing_ratio=0.617398（timing_v4_i4_q3z，来源 timing_layer_audit.jsonl 单行）。
- 快照 paper-state.json.bak-task0486-20260825：内容同现行但 last_daily=08-21。

### B. 成本相关硬数据
1. **旧引擎 08-10 批次（paper-trades.csv L2-L11）**：10 笔 BUY，fee=amount×0.03%（逐笔验证：9736×0.0003=2.92 ✓）。总成交额 99141，总 fee 约 29.74。费率口径=单边 0.03%，与 v2 假设（佣金0.10%+价差0.03%）不一致——旧引擎未计佣金。
2. **新引擎 08-14 批次（paper-state.json holdings）**：sum(shares×cost)=59567；cash 缺口 = 100000−40393−59567 = 40 元。若为佣金：59567×0.03%=17.87 < 每笔最低 5 元×8 笔=40 ✓ 精确吻合。=> 新引擎按"最低佣金 ¥5/笔 + 0.03%"或类似规则收费。实际单边成本 40/59567=0.0671%。
3. trades.csv 未记录 08-14 批次（数据缺口①）：新引擎成交只落在 state 文件，无逐笔 trades 流水。
4. engines/gold/paper_state.json：w=0.0 未持仓，零摩擦；frozen_form.cost_per_absdw=0.0013 与 v2 一致（溯源：engines/gold/paper_state.json frozen_form 节）。

### C. 估值质量疑点（审计发现②）
- paper-nav.csv L2-L7：08-14→08-21 六个交易日 nav 全部=0.9996、holdings_value 全部=59567 —— 每日 mark 为停更态（bak 文件同样）。
- 08-24 首次真实重估：holdings 57926（较成本 −1641），nav 0.9832。
- 状态不一致③：state.updated_at=2026-08-26T16:30 / last_data_date=08-25 / last_daily=08-25，但 nav.csv 与 summary 止于 08-24。

