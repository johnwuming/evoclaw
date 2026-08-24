2026-08-25 05:51:07 [R-309/task-0487] 启动：旧链 paper_trade.py 退役 + 在役链冒烟验证

## 1. 环境与现状（2026-08-25 05:51 GMT+8）
- SSH 连通：noname@10.12.192.174，主机名 nonameopenclawhomebase，UTC 时区（当地 2026-08-24 21:51）
- crontab 共 36 行，已落盘 /tmp/hp-crontab-before.txt（VPS 侧）
- 目标行定位（恰好 2 行匹配 paper_trade|cron_paper_rebalance）：
  - L3: `30 16 * * 1-5 cd /home/noname/quant-evolve && .../python3 scripts/paper_trade.py --action daily >> logs/cron_daily.log 2>&1`
  - L5: `30 16 * * 1-5 cd /home/noname/quant-evolve && .../cron_paper_rebalance.sh >> logs/cron_rebalance.log 2>&1`

## 2. crontab 退役（步骤1）✅
- 备份：HP `~/quant-evolve/results/archive/crontab.bak.r309-202608242151`（5103B, 36 行）
- 移除方式：`crontab -l | grep -v "scripts/paper_trade.py --action daily" | grep -v "scripts/cron_paper_rebalance.sh" | crontab -`（未用 crontab -r）
- 验证：写回后 34 行；`grep -c "paper_trade\|cron_paper_rebalance"` = 0
- diff 备份 vs 现状：仅 `3d2`（paper_trade daily 行）与 `5d3`（cron_paper_rebalance.sh 行）两个删除，无任何其他行变化 → 恰好少 2 行 ✅

## 3. 旧链产物归档（步骤2）✅
- results/paper-nav.csv（329B, 2026-08-24 17:40Z）→ archive/paper-nav.csv.r309-retired
- results/paper-summary.json（1307B）→ archive/paper-summary.json.r309-retired
- mv 前用 lsof 确认无进程持有两文件（输出为空）
- results/ 下原路径已不存在（ls 报 No such file）；archive/ 内 r309 三件套 + README-r309.md（1251B，含退役原因+指向 R-308/R-309 报告）齐备

## 4. cron 脚本处置（步骤3）✅
- scripts/cron_paper_daily.sh 与 cron_paper_rebalance.sh 未删除，均在文件首行插入：
  `# RETIRED by task-0487 R-309 2026-08-25: crontab 已移除引用，旧链退役留档，勿再启用`
- 其余内容未动；crontab 已无任何引用，纯留档

## 5. 在役链冒烟验证（步骤4）
### 5.1 validate ✅
- 命令：`quant/bin/python scripts/paper_engine.py --action validate`（2026-08-24 21:52 UTC）
- 结果 **6 PASS / 0 FAIL，退出码 0**（预期 5/6，K线新鲜度预期 FAIL 为已知环境问题——实际当日 K 线已采集，最新交易日 2026-08-24 距今 0 天，PASS；优于预期）
- 明细：K线新鲜度 P / 因子面板覆盖率 P（5028只，非空率全1.0）/ 持仓K线完整 P（8只0异常）/ 价格合理 P（209抽样0异常）/ 分红连续 P（4461条）/ 调仓选股 P（20只）

### 5.2 daily 幂等 ✅（2026-08-24 21:54 UTC）
- pre 基线：baseline-paper-nav.csv 8 行，末行 `2026-08-24,0.98319`；paper-state.json last_daily=2026-08-24、model_version=a13_rsraw_e1f10dz
- 执行 `--action daily`：日志「spot 收盘价拉取失败（回退 parquet 口径）」→ 优雅降级重算；「✅ rsync 到 VPS 完成」「净值更新: 总资产 ¥98,319.00 | NAV 0.983190 | 持仓 8 只 | 模型 a13_rsraw_e1f10dz」退出码 0
- post：仍 8 行（未追加、无重复），末行/last_daily/model_version 逐字不变 → 幂等正确（HP 为 UTC，2026-08-24 行已存在，重算值与既有值一致）
