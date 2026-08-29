# task-0564 工作笔记：8-29 qfq 收盘源入库后补跑 equity daily + mirror + recon + BFF 验证

- 开工时间：2026-08-29 20:44 (GMT+8)
- 背景：task-0556 发现 8-29 在役日更 cron 触发但当日 NAV 行未生成（qfq 收盘源未及时入库）。触发窗口今晚 20:30 后手动补跑。
- 纪律：HP 在役进程勿杀；禁改 crontab/registry/paper_engine/引擎文件/权威文件历史行；curl 截断；SSH 输出 ≤30 行；边查边写。

## 步骤 0：先例文档定位

## 步骤 0 结果：先例与命令定位（20:45）

- 在役日更 cron（只读查得，禁改）：`30 16 * * 1-5 cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine.py --action daily >> ~/quant-evolve/logs/paper_daily.log 2>&1`
- qfq 收盘源入库 cron：`0 18 * * 1-5 ... scripts/cron_qfq_daily.py`（今晚 16:30 daily 触发时源未入库 → 缺口；现需确认源已补齐）
- 镜像命令（R-354/runbook 先例）：`portfolio_v1/governance/governance.py mirror`——按 date 去重增量翻译 baseline CSV 新行 → nav.daily/trade.fill 追加，复跑幂等；watch 常驻监视器 17:05 已自退出，需手动触发
- recon：`governance.py recon`（R-354 先例 PASS，两个如实降级 cash_band/weight_sums）
- BFF navseries（R-358）：VPS 端点 GET /api/v1/portfolios/vC-0/navseries，源=镜像副本 /root/.openclaw/workspace-quant/results/baseline-paper-nav.csv，同步用 auto_sync_notify.py --job-name cron-auto-sync
- 8/28 先例：官方 NAV=1.00993（R-354 补跑产出）

## 步骤 1：查 qfq 源 8-29 数据

### 结论：qfq 源无 8-29 数据 → 触发停止路径（20:50）

**证据链：**
1. `date -d 2026-08-29` = **星期六**（A 股非交易日）；8-28 = 星期五。
2. qfq 日更文件抽样 max 日期 = **2026-08-28**（000001/600519/000848/300750 四只 `_daily_qfq.parquet` 一致；另注意裸 `<code>.parquet` 为旧文件止于 8-21，日更写 `*_daily_qfq.parquet`）。
3. HP `logs/cron_qfq_daily.log` 止于 2026-08-28 18:15：STAGE1/2 rc=0、GATE ref=2026-08-28 fresh=5/5——8-28 收盘源当日已入库完毕；8-29（周六）cron `0 18 * * 1-5` 不调度，无新数据。
4. HP `logs/paper_daily.log` 止于 2026-08-28 16:30（该次回填 8-27 行 NAV 0.9984）；8-29 16:30 在役 daily cron 调度为 `30 16 * * 1-5`，**周六不触发**——任务书前提「8-29 16:30 cron 有触发」与 crontab 事实不符。
5. 权威 `baseline-paper-nav.csv` 末行 = `2026-08-28,1.00993`（R-354 昨日已补 8-28），止于此为周六正确状态。

**按步骤 1 停止路径处置：**
- 不补跑 equity daily（qfq 源无 8-29 行情，强跑仅空转或重复 8-28 行，污染在役底账风险）；
- 不手动触发镜像追加（权威 CSV 无 8-29 新行可翻译，无缺口可补）；
- 下一个交易日 8-31（周一）16:30 在役 daily 自然生成 8-31 行，链路无遗留缺口；
- R-358 先例亦已记录「8/29 周六无交易日，数据已最新」，与本次结论互证。

**任务状态：paused（源无数据，非故障缺口）。**

## 只读佐证（不做写动作）
