# task-0434 过程笔记（监控库瘦身）

- 开工：2026-08-21 19:58，任务置 running
- 现场：metrics.db 340,303,872B + WAL 262,023,792B；hp 1,165,406 行(08-20T00:00:01Z→08-21T11:57:01Z) vs vps 2,146 行(→11:59:01Z)，重复约 539 倍，与主 agent 诊断一致
- 根因确认：pull-hp-metrics.sh 每 2 分钟 ATTACH hp.db 后 `INSERT OR IGNORE ... WHERE server='hp'` 全量重插；system_metrics 无 UNIQUE 约束（仅自增 PK），OR IGNORE 无效；HP 侧另每分钟直报 /api/metrics/ingest 双通道叠加

