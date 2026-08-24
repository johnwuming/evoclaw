# task-0486 模拟实盘超期修复+完整性核查 notes
开始: 2026-08-25 00:51 GMT+8

## 阶段0: 环境确认
- 待办

## 阶段1: VPS 侧副本核查（2026-08-25 01:03）

### paper-state.json（1.1KB）
- model_version=a13_rsraw_e1f10dz, initial=100000, cash=40393, 8 持仓 buy_date=2026-08-14
- last_daily=2026-08-21, last_rebalance=2026-08-14
- **updated_at=2026-08-24T16:30:21（周一引擎确实运行了，但 last_daily 未推进 → 追加门嫌疑实锤）**
- timing_ratio=0.617398, timing_layer=timing_v4_i4_q3z（summary 中）

### baseline-paper-nav.csv（84B，仅 4 行）
- 日期：08-14, 08-19, 08-20, 08-21（nav=0.9996/0.98879/1.00892/0.98989）
- 缺口：08-17(创建日16:09), 08-18(周二), 08-22/23(周末OK), 08-24(周一，today 08-25)
- 缺口交易日：08-17?（引擎当天16:09才建，可辩解）、08-18、08-24

### 双引擎现象（VPS 副本证据）
1. **新链路**：baseline-paper-{nav.csv, portfolio.json, summary.json} + paper-state.json
   - summary: updated_at=2026-08-24T16:30:03, price_date=2026-08-21, total_asset=98989, model_version=a13_rsraw_e1f10dz
2. **旧链路**：paper-nav.csv / paper-portfolio.json / paper-summary.json / paper-trades.csv
   - paper-portfolio.json mtime=08-12 02:53（老系统）
   - paper-nav.csv: 08-14,08-19,08-20,08-21 四行，但 nav 全部 0.9996 冻结在成本价（pnl=0），last_update=2026-08-21
   - paper-nav.csv mtime=08-25 00:30（同步时间戳），需 HP 侧确认是否仍在被写

### 待查（HP 侧）
- [ ] baseline-paper 引擎脚本与追加门逻辑
- [ ] 旧 paper 引擎是否仍在 cron 运行、谁在写
- [ ] versions-manifest.json 的 paper 记录
- [ ] baseline-paper-validation.json（8-24 04:01, 3.6KB）内容
