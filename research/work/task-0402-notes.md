# task-0402 过程笔记：qfq 日更采集实施 + ZeroTier UFW 放行

- 日期：2026-08-20 00:12 起（用户 00:06 批准推进）
- 方案来源：R-244（§4.1 方案 A + §4.2 qfq 日更方案）
- 预算：子 agent 硬上限 1 小时，按 ≤40 分钟设计

## 1. UFW 放行（VPS 本机）✅ 完成

**变更前快照**：`/tmp/task0402-ufw-before.txt`（18 条规则，active，无任何 22 端口放行——与 R-244 结论一致）

**新增规则（最小面：仅 ZT 接口 + 内网网段 → 22）**：
```
/usr/sbin/ufw allow in on ztfl6eg7ba from 10.12.192.0/24 to any port 22 proto tcp
```
变更后 grep：`[10] 22/tcp on ztfl6eg7ba  ALLOW IN  10.12.192.0/24`，快照 `/tmp/task0402-ufw-after.txt`。

- 公网 22 无新放行（公网暴露面不变，符合入侵史红线）
- 未开放其他端口

**连通实测（HP → VPS 10.12.192.98:22）**：`HP_TO_VPS_SSH_OK / VM-0-11-ubuntu` ✅（此前 R-244 证据链中该路径 100% 被 DROP）

**回滚命令**：
```
/usr/sbin/ufw status numbered   # 找到 22/tcp on ztfl6eg7ba 行号 N
/usr/sbin/ufw delete N          # 即恢复变更前状态
```

## 2. HP 侧现状探查

- crontab 完整快照：见 §2.1（落盘 HP /tmp/task0402-crontab-before.txt + 本文件摘要）
- 现有脚本：`scripts/collect_qfq_baostock.py`（10406B，含 .bak.20260819 备份）
- metrics 通道：`* * * * * COLLECT_VPS_URL=http://82.156.124.186:8055 .../collect-metrics.sh hp`（每分钟）
- 通知聚合：`scripts/notify_hub.py`（W8）

### 2.1 crontab 现有行摘要（改动前）
- `30 16 * * 1-5` paper_trade.py --action daily
- `30 16 * * 1-5` cron_paper_rebalance.sh
- `0 20 * * 0` refresh_data.py（akshare，失效源，保留不动）
- `0 2 1,15 * *` p3_3_evolution_standalone
- `30 16 * * 1-5` paper_engine.py --action daily
- `0 20 * * 0` paper_engine.py --action validate
- `* * * * *` collect-metrics.sh hp
- `30 6 * * 0` fetch_valuation_data.py
- `45 16 * * 1-5` risk_patrol.py
- `0 7 * * 0` collect_crowding.py
- `0 9 * * 6` evolution_pipeline.py cycle
- （W8 notify_hub 等行待完整快照确认）

（待续：脚本设计、cron 安装、首跑验证）
