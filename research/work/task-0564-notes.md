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
