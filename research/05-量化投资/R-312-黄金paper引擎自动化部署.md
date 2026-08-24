# R-312 黄金 paper 引擎逐日自动化 cron 部署（9/1 首调仓前）+ 周度 verify

- 任务号：task-0490（任务中心 127.0.0.1:8055）
- 日期：2026-08-25（执行窗口 UTC 2026-08-24 22:03–22:11 = CST 08-25 06:03–06:11）
- 链路：黄金趋势引擎链路（gold_trend_sma200）自动化收尾
- 执行人：子 agent（主会话分派）；用户 2026-08-25 05:54「黄金引擎推进」批准

## 背景

R-307（task-0485，已验收）已将黄金趋势引擎激活为 registry active 并部署自包含 paper 引擎 `scripts/paper_engine_gold.py`（16.4KB，--action init/daily/monthly/verify，daily 含跨月自动结账/调仓，数据自取腾讯 fqkline sh518880 全量拉取，不依赖 parquet 新鲜度），完成首跑 init+daily 验证。**遗留项**：逐日自动化 cron 当时守安装边界未装（不在 INSTALL.md 待装包内），paper 引擎激活后若无人跑 daily，marks 链会缺日、NAV 链断裂。**硬期限**：2026-09-01（周二）首个交易日，引擎将自动跨月结账+调仓，cron 必须在此前就位。当前 state：`results/engines/gold/paper_state.json` status=active_paper、current_weight=0.0（全现金）、marks=1（2026-08-24 px=9.5640），8-24 收盘价已逼近 SMA200≈9.479，若 8-31 月末突破，9/1 将建仓。本任务与并行 R-310（paper_engine.py 备用行情源）文件不相交：仅动 HP crontab（+2 行），未触碰 paper_engine_gold.py / paper_engine.py / registry / evolution_pipeline.py。

## 方法

1. **冲突检查**：拉取 HP crontab 全文（34 行，与 R-309 交接一致）落盘 `/tmp/r312-crontab-before.txt`，枚举 hour=3/7/16 全部条目核对时间窗。
2. **计划设计**（理由见下表），与在役链路错峰。
3. **管道安装**（严禁 `crontab -r`）：先备份 `results/archive/crontab.bak.r312-$(date +%Y%m%d%H%M)`，再 `(crontab -l; echo L1; echo L2) > /tmp/r312-newcron && crontab /tmp/r312-newcron`，diff 确认恰好 +2 行。
4. **部署后验证**：手动 daily ×1（幂等）→ 二次 daily → 字段级 diff（python 递归对比 state JSON）→ verify（引擎自检全 True）。

### cron 计划设计理由

| 行 | 计划 | 理由 |
|---|---|---|
| gold daily | `40 7 * * 1-5`（UTC） | = CST 15:40 周一~五，A股 15:00 收盘后 40 分钟，腾讯 sh518880 fqkline 日线已可得；避开在役 paper_engine 16:30 UTC 与 risk_patrol 16:45 UTC 时段；现有 crontab 工作日 07:xx UTC 全空，零冲突 |
| gold verify | `0 3 * * 0`（UTC） | = 周日 11:00 CST 低负载时段；与周日 07:00 UTC collect_crowding 错开 4 小时；hour=3 现有 crontab 全空；verify 失败按任务书仅留日志可见（`logs/paper_gold_verify.log`），不配自动通知 |

命令体：`cd ~/quant-evolve && ~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action daily >> logs/paper_gold_daily.log 2>&1`（verify 同构，日志 `logs/paper_gold_verify.log`）。HP 时区为 UTC，故直接写 UTC 时刻，无需换算适配。

## 核心发现 / 执行结果

1. **安装精确 +2**：部署后 crontab 36 行；`grep -c paper_engine_gold` = 2；`diff 备份 <(crontab -l)` 仅 `34a35,36`，前 34 行逐字不变。备份文件：`~/quant-evolve/results/archive/crontab.bak.r312-202608242207`。
2. **daily 幂等三重确证**：当前（CST 08-25 盘前）最新完整日线仍为 08-24（已标记），三次手动 daily 均输出 `mark 2026-08-24: px=9.5640 ... [dup: 未重复记账]`，exit=0；marks_n 前后均 =1，status=active_paper、current_weight=0.0 不变；**字段级递归 diff 第 2/3 次 daily 前后 state JSON，唯一变动 `/updated_at` 时间戳，marks/open/nav/weight 逐字节相同**。
3. **verify 全 True**：`w_state=0.0000 w_signal=0.0000 match=True; nav_chain=True; nav_open=True; marks=True; months_closed=0`，exit=0。audit 仍 1 条（init），daily dup 不写审计，符合 append-only 设计。
4. **无冲突复核**：hour=7 工作日无既有条目；hour=3 全空；与 `30 16 * * 1-5` paper_engine、`45 16 * * 1-5` risk_patrol、`0 7 * * 0` collect_crowding 全部错开。

## 9/1 调仓预案（说明，未执行）

- 9/1（周二）15:40 CST，cron 首次自动触发 daily：引擎检测 8 月→9 月跨月 → 自动结账 8 月（stub 月，basis 2026-08-24、price_ref 9.564、w=0）→ 按 8-31 月末冻结信号（PIT）调仓。
- 仓位走向：7-31 时 px=8.433 < SMA200=9.479 → w_signal=0（当前全现金与之一致）；8 月金价 +13.4%（部分月），8-24 px=9.5640 已在 SMA200 附近。**若 8-31 收盘 px>SMA200 且 vol60 达标 → w 从 0 升至 vol_target(10%)/vol60_ann 对应目标仓位**，触发买入 518880（|Δw|×0.13% 成本入账）；否则维持全现金吃货基 MMF 收益。
- 人工复核命令（9/1 后抽查）：
  - `~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action verify`（应全 True 且 months_closed 增至 1）
  - `~/miniconda3/envs/quant/bin/python scripts/paper_engine_gold.py --action monthly`（月度摘要：结账+调仓+audit）
  - `tail -20 ~/quant-evolve/logs/paper_gold_daily.log`（cron 首次自动运行留痕）
- 回滚：`crontab ~/quant-evolve/results/archive/crontab.bak.r312-202608242207` 即恢复 R-309 终态（34 行）。

## 结论

R-312 完成：黄金 paper 引擎逐日自动化（工作日 15:40 CST daily）+ 周度 verify（周日 11:00 CST）已在 HP crontab 就位，**恰 +2 行、零改其余**，幂等性与自检均实测通过，2026-09-01 首个交易日跨月结账+调仓将由 cron 自动执行（引擎层自包含，无需人工介入）。黄金链路自动化至此闭环：信号生成（cron 3 日 append/evaluate）→ paper 记账（本次 daily/verify）→ 人工复核命令已备。真金分配仍为独立人工门，未涉及。

## 来源

- HP 主机 noname@10.12.192.174（UTC）：crontab（36 行）、`~/quant-evolve/scripts/paper_engine_gold.py`、`results/engines/gold/paper_state.json`、备份 `results/archive/crontab.bak.r312-202608242207`
- 过程笔记（含部署后 crontab 36 行全文快照）：`shared/results/work/task-0490-notes.md`
- 前置：R-307 激活报告 `05-量化投资/R-307-黄金趋势引擎激活实施.md`；R-309 收敛报告（crontab 34 行基线）
