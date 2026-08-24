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

## 阶段1: 根因定位（已完成，证据充分）

### 事实链
1. CSV 现状: header+4行 (08-14/19/20/21)，全部 NAV=0.9996 cash=40393 hv=59567 total=99960（成本价估值，无价格波动）
2. cron_daily.log: 08-17/18/19/20/21/24 每日 16:30 daily 全部跑完退出（无异常），输出值完全相同 99960/0.9996/59567/40393
   → "跑完但没追加"确认为「行日期取数据日期→去重覆盖旧行」
3. paper_trade.py action_daily 关键代码（~L602-610）:
   latest_date = str(df_latest["date"].iloc[0])  ← 取 glob 排序第一个文件(000001.parquet)尾行日期，非今天
   save_nav(latest_date, ...) → save_nav 去重"同日只保留最后一条"
4. 数据现状: data/all_stocks_qfq/ 双命名并存:
   - {code}.parquet 批量管线(~5254文件, mtime 08-23 20:00 批量, 数据尾=08-21)
   - {code}_daily_qfq.parquet 日更管线(R-244, 08-23 18:00 后 08-24 18:00 仅 775/5448 更新)
   - 000001.parquet 尾行=2026-08-21
5. **根因A（追加门/日期错位）**: daily 以数据尾行日期作 NAV 行日期。数据滞后 1 个交易日（16:30 跑、18:00 更新 qfq）+ 批量管线周末才更新 → 每日运行把值写到"昨天"的行上，最新交易日永远缺行。08-17/18 写到 08-14 行（数据仍停 08-14），08-24 写到 08-21 行。
6. **根因B（成本价回退→NAV 冻结）**: 持仓 8 只代码(300824 等)在数据目录只存在 {code}_daily_qfq.parquet，而 load_all_latest_data 的 code=basename 去 .parquet 后含 "_daily_qfq" 后缀 → state["holdings"] 键(纯代码)匹配失败 → 全部走成本价回退分支 → 市值恒=59567(=Σshares×cost 精确验证) → NAV 一周冻结 0.9996。
7. 文件数 6030→5448 变化发生在 08-17（task-0347/R-220#37 维护窗口，cron_paper_rebalance.sh 有 .bak-r220n37-20260817 备份，state.created_at=08-17T16:09:39 重置）→ 数据布局变更后 paper_trade 未适配新命名。

### 双引擎文件矩阵
- paper_trade.py (task-0347): 写 paper-state.json / paper-trades.csv / paper-nav.csv / paper-summary.json / factor-db.json；cron 16:30 工作日
- paper_engine.py v3 (task-0251): 写 **paper-state.json(共享!)** / baseline-paper-{summary,nav,trades,portfolio,validation}.json|csv；cron 16:30 同刻 + 15:00 月首调仓 + 周日20:00 validate
- **共享 state 竞争确证**: last_daily 字段只有 paper_engine 写(L1198)；当前 state last_daily=08-21 而 v3 08-24 实际写了 08-24 → 被 paper_trade 16:30:21 的 save_state 覆盖回 08-21（经典 lost-update：两进程 16:30:02 同时 load，v3 :05 save，trade :21 save）
- v3 (baseline-paper-nav.csv): 4行 08-14=0.9996/08-19=0.98879/08-20=1.00892/08-21=0.98989；行日期=trading_calendar()口径（同样数据驱动滞后一天：08-24 run 写 08-21 行）；值=holdings_value_at(d) 按数据日收盘计价，(日期,值)内部自洽
- v3 daily 也有真实估值（0.9888~1.0089 波动）→ v3 的 holdings_value_at 能拿到价格（用日更数据?）
- VPS 镜像(04-投资研究/): baseline-paper-* 与 paper-nav/state/summary 新鲜(08-25 00:30 有同步)；paper-portfolio.json+paper-trades.csv 陈旧(08-12)——因 paper-* rsync 只在 cron_paper_rebalance.sh 调仓日执行，08-14/17 调仓后 trades 未同步

### 08-14 行真相
当前 CSV 的 08-14 行是 08-17 run 写入（成本价 59567），覆盖了 08-14 当日 run 的真实估值行（11持仓/95124/NAV0.9999，见 cron_daily.log L68）→ 历史真实数据已被覆盖，只能标注

