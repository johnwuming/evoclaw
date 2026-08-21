# task-0434 过程笔记（监控库瘦身）

- 开工：2026-08-21 19:58，任务置 running
- 现场：metrics.db 340,303,872B + WAL 262,023,792B；hp 1,165,406 行(08-20T00:00:01Z→08-21T11:57:01Z) vs vps 2,146 行(→11:59:01Z)，重复约 539 倍，与主 agent 诊断一致
- 根因确认：pull-hp-metrics.sh 每 2 分钟 ATTACH hp.db 后 `INSERT OR IGNORE ... WHERE server='hp'` 全量重插；system_metrics 无 UNIQUE 约束（仅自增 PK），OR IGNORE 无效；HP 侧另每分钟直报 /api/metrics/ingest 双通道叠加


## 步骤1：pull-hp-metrics.sh 修复（19:59 完成）
- 原版备份：/tmp/pull-hp-metrics.sh.orig-task0434（脚本未被 git 跟踪，diff 用此文件）
- 改动：①watermark 增量拉取（scripts/pull-hp-metrics.watermark，缺失时用 VPS 库 hp 最大时间戳兜底，防首轮全量）②密码改读 secrets.env QUANT_SSH_PASSWORD（已实测 SSH 登录 OK）③合并 SQL 加 timestamp > watermark 条件，OR IGNORE 保留 ④node 回退路径同步改 ⑤bash -n 通过
- cron 未动（*/2），server.js 未动

## 步骤2：metrics.db 瘦身
