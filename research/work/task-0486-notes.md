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


## 阶段2: 修复实施与验证（已完成）

### 补丁内容（paper_trade.py, +2.4KB, 4处）
1. L80 代码匹配: basename 去 .parquet 后再去 `_daily_qfq` 后缀 → 持仓纯代码可命中日更文件价格
2. L146-156 双源去重: 同代码 {code}.parquet(批量) vs {code}_daily_qfq.parquet(日更) 保留数据日期更新行
3. L473-487 save_state 写前重读合并 {**disk, **state} → 缓解与 v3 同刻写共享 paper-state.json 的 lost-update
4. L626-644 NAV 行日期=运行日(工作日)；周末手动运行回退数据日期防误写；数据滞后降级为告警；state 新增 last_daily+last_data_date

### 备份
HP: scripts/paper_trade.py.bak-task0486-20260825 (31768B, md5 2b96a20c 与原文件一致)
本地: /tmp/paper_trade_orig.py

### 验证（沙箱 /tmp/t486，未触生产文件）
- 干跑 action_daily（真实数据+复刻 state）两次，结果一致：
  - NAV csv 追加 `2026-08-24,0.9899,40393.0,58596.0,98989.0`（旧代码会写 08-21 行=覆盖）
  - 持仓市值 58596 ≠ 成本 59567 → 价格命中（修复前恒成本）
  - **交叉验证**: 98,989.00 与 v3 paper_engine 08-24 16:30:05 独立计算的总资产完全一致（两引擎估值收敛）
  - last_daily=2026-08-24；v3 独有字段(model_version_from_v3_test)写后保留
  - last_data_date=2026-08-24（部分日更文件已含当日数据）
- py_compile 通过（本地+HP 双侧）

## 阶段2: HP 侧根因诊断（01:05-01:10）

### 引擎与 cron 结构（HP crontab）
- **paper_engine.py（新链路, task-0251）**：16:30 daily / 15:00 rebalance --check-month-start / 周日20:00 validate
  - 写 baseline-paper-{nav,portfolio,summary,trades,validation} + paper-state.json，自带 rsync 到 VPS
- **paper_trade.py（旧链路）**：16:30 daily（cron_daily.log），写 paper-{nav,summary,portfolio}.csv/json + cron_paper_rebalance.sh
- **数据管道**：cron_qfq_daily.py 18:00(1-5) 增量刷 data/all_stocks_qfq/（stage1=持仓+hs300 294只~71s；stage2=全市场~894s）；周日18:00 collect_qfq_baostock --mode init + rebuild_merged；周日20:00 refresh_data.py

### 根因（追加门 bug 定位，已复现于日志+代码）
1. **action_daily() 行日期 = get_latest_trade_date() = parquet 数据最大日期**（paper_engine.py L1191: d=get_latest_trade_date() → L1199 append_nav(str(d))）
2. **数据时序错位**：引擎 16:30 跑，但 qfq 数据 18:00 才刷新 → 引擎永远用 T-1 数据 → 行日期永远滞后
3. **叠加数据管道缺勤**：cron_qfq_daily.log 最后一次成功=08-21 18:16（数据到 08-21）；**08-24(周一) 18:00 无任何日志行=未运行**；parquet 实测 max date=2026-08-21（000001/300824/601600/002027 全部）
4. 结果：08-24 16:30 引擎用 08-21 数据算 NAV(98,989/0.98989) → append_nav upsert 行日期 08-21（该行系 08-24 运行写入）→ 08-24 行缺失，last_daily 停在 08-21
5. **历史缺口同因**：08-17、08-18 行缺失（08-17 周一 18:00 qfq 刷新未跑 + 结构性滞后）；已存在行 08-19/08-20/08-21 分别由 08-20/08-21/08-24 的运行写入（NAV 值与逐日日志完全吻合，已交叉验证）
6. append_nav 本身是 upsert（按日期去重后重写），不会产生重复行；问题不在去重，在行日期取的是"数据日期"而非"运行交易日"

### 旧引擎（paper_trade.py）状态
- 16:30 照跑（cron_daily.log 08-24 有完整运行），但 NAV 恒 0.9996/99960 冻结在成本价（pnl=0，加载 6089 文件后价格未生效）→ 价格查找静默失败回退 cost
- 其输出 paper-nav/paper-summary 与新链路并存 = 双引擎现象

### 待办
- [ ] 消费者排查：谁读 baseline-paper-* vs paper-*
- [ ] akshare 可用性
- [ ] cron_qfq_daily.py 参数（能否只跑 stage1）

## 阶段3: 回填与生产应用（已完成）
1. 生产 dry：08-24 17:23 用补丁版跑 --action daily（写前已 cp 备份 nav/state 各 .bak-task0486-20260825）
   → 08-24 行 = 0.9899/58596/98989（市值计价，与 v3 同日独立计算 98,989 完全一致）
2. 回填 08-17/08-18 行：值取 cron_daily.log 当日 run 输出（99960/59567/40393/0.9996，成本价口径），python 插入+排序+断言无重复
3. CSV 终态 7 数据行（08-14/17/18/19/20/21/24），cash+hv=total 校验通过
4. state: last_daily=08-24, last_data_date=08-24, model_version 保留（合并写生效）
5. summary 刷新：nav_per_unit 0.9899, last_update 08-24
6. VPS 镜像：HP→VPS rsync 255 失败（ssh subsystem 关闭），改 VPS 侧 pull 成功；paper-nav.csv(329B)/state(1135B)/summary(1306B) 均为最新

## 阶段4: 审计补充
- backup_paper_state_20260812/: 旧 v1 schema（current_capital/factor_model/rebalance_schedule，无 cash/holdings），与现行 state 完全不同代际，对当前引擎不可作回滚点（仅历史考古价值）；其 paper-nav.csv 仅 2 行
- qfq 日更 cron（R-244, 18:00 两阶段）最后成功 08-21 18:16；HP 当前时间 17:25 08-24（周一），今日 18:00 尚未到——非故障
- 周日批：collect_qfq_baostock init + rebuild_merged（20:00 周日）→ 5254 文件 mtime 08-23 20:00，数据尾=08-21
- 无关文件零改动；crontab 未动；gold/registry/engines/evolution_pipeline 未触碰

## cron/链路待办（交主 agent，本任务不改 crontab）
1. paper_trade.py 与 paper_engine.py 同刻 16:30 双跑：建议错峰（如 paper_trade 16:35）或收敛单引擎（见报告权威源建议）
2. VPS 镜像 paper-trades.csv/paper-portfolio.json 停在 08-12（rebalance 日才 rsync paper-*；08-14/17 调仓未同步）——建议 daily 后也同步这两个文件
3. HP→VPS root rsync 当前 255（io/subsystem），v3 的 rsync_to_vps 在 16:30 却显示成功——两者路径/方式不同，需核对（可能 v3 走了别的用户/端口）
4. 000001_daily_qfq.parquet 与 000001.parquet 双源并存：合并口径已由本补丁在 paper_trade 侧处理；上游 rebuild_merged 归一时点（周日）与日更的关系建议复核
