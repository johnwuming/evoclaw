# task-0434 过程笔记（监控库瘦身）

- 开工：2026-08-21 19:58，任务置 running
- 现场：metrics.db 340,303,872B + WAL 262,023,792B；hp 1,165,406 行(08-20T00:00:01Z→08-21T11:57:01Z) vs vps 2,146 行(→11:59:01Z)，重复约 539 倍，与主 agent 诊断一致
- 根因确认：pull-hp-metrics.sh 每 2 分钟 ATTACH hp.db 后 `INSERT OR IGNORE ... WHERE server='hp'` 全量重插；system_metrics 无 UNIQUE 约束（仅自增 PK），OR IGNORE 无效；HP 侧另每分钟直报 /api/metrics/ingest 双通道叠加


## 步骤1：pull-hp-metrics.sh 修复（19:59 完成）
- 原版备份：/tmp/pull-hp-metrics.sh.orig-task0434（脚本未被 git 跟踪，diff 用此文件）
- 改动：①watermark 增量拉取（scripts/pull-hp-metrics.watermark，缺失时用 VPS 库 hp 最大时间戳兜底，防首轮全量）②密码改读 secrets.env QUANT_SSH_PASSWORD（已实测 SSH 登录 OK）③合并 SQL 加 timestamp > watermark 条件，OR IGNORE 保留 ④node 回退路径同步改 ⑤bash -n 通过
- cron 未动（*/2），server.js 未动

## 步骤2：metrics.db 瘦身
- 20:10 备份：checkpoint(TRUNCATE) 后 WAL 262MB→0；cp 至 /root/metrics.db.bak-task0434-20260821（340MB，integrity_check=ok，1,176,214 行）
- 20:15 发现并修复新脚本 bug：dot-command `.timeout` 不能放 SQL 参数串（20:00-20:14 七次合并失败）；改用 `sqlite3 -cmd ".timeout 5000"`，20:16 起恢复正常
- 20:18 验证增量生效：watermark=2026-08-21T12:18:01Z，hp 12:06Z 起每分钟恰好 1 行（此前 539 倍重复 → 1 倍）
- 旁路发现（非本任务改动面）：HP 直报通道 12:05Z 后断流（12:00-12:02 有 3/2/1 份重试补发重复），属 server.js/HP 侧（task-0433 并行范围），已在收尾原子事务中一并去重；唯一索引生效后双通道同分钟数据将由 OR IGNORE 幂等吸收
- 保留集：4,321 组 (timestamp,server)（只读 GROUP BY 实测 0.6s）

### 手术执行（20:19-20:25）
- keep 表放独立 attached 库 /tmp/t0434_keep.db（读写分离：只读扫主库、写只落附库，主库零长锁）；保留集 4,350 组，快照 MAXID_KEPT=8,276,635
- 分批 DELETE：22 批 × 10 万行 id 区间，共删 1,072,091 行，每批短事务（~1s），服务写入无中断（vps ingest 期间持续正常）
- 原子收尾（BEGIN IMMEDIATE 单事务 0.026s）：残余去重 0 行（分批已删净）+ CREATE UNIQUE INDEX idx_uniq_ts_server ON system_metrics(timestamp,server) 建成（unique=1，PRAGMA index_list 确认）——索引建成即证明零重复
- checkpoint(TRUNCATE) + VACUUM(0.046s) + checkpoint：**metrics.db 340,303,872B → 823,296B（340MB→0.8MB，超额达标，目标 <5MB）**，WAL 262MB→0，integrity_check=ok
- 终态行数：4,352（hp 2,184 + vps 2,168），时间跨度 08-20T00:00:01Z → 当前，每 (timestamp,server) 恰 1 行
- keep 临时库已清理；备份保留 /root/metrics.db.bak-task0434-20260821（确认稳定后可删）

### API 验证（20:27）
- GET /api/metrics/system/current → 200，9.6ms
- GET /api/metrics/system?hours=24 → 200，71ms，servers=[hp,vps]，各 287 个 5min 降采样点，字段完整（cpu/mem/disk/net/temp）→ 24h 趋势图数据完整

### 增速回归验证（20:30-20:35，覆盖 20:30/20:32/20:34 三个 pull 周期）
- t0 20:30:18 = 4,364 行 → t1 20:34:43 = 4,373 行：**+9 行/4.4 分钟 ≈ +2 行/分钟**（hp 1 + vps 1），修复前为 ~+1000 行/分钟（539 倍重复）
- hp 12:24Z→12:34Z 每分钟恰好 1 行；hp_max/vps_max 均追平当前分钟；watermark 持续推进（12:34:01Z）
- pull 日志最后一条错误停在 20:14（修复前），此后零错误
- 终态：metrics.db 831,488B（0.83MB）+ WAL 0（checkpoint 后），integrity ok；prune 每小时滚动后会稳定在 ~2,880 行（24h×2 台×1 行/分钟）

### 「只保持一条数据可以吗」评估结论
**不建议。** 监控卡是 24h 趋势图（全部/VPS/HP 三种过滤），只留 1 条 = 趋势卡退化成静态数字卡，等于废掉监控功能。合理上限 = 1 行/分钟/台 × 24h × 2 台 ≈ 2,880 行 ≈ 1MB 以内。本次瘦身后实际 0.83MB/4,373 行，已在目标量级——**无需「只留一条」即可达标**。

### 交付清单
- 修复：scripts/pull-hp-metrics.sh（watermark 增量 + 密码外置 secrets.env + OR IGNORE 双保险；原版备份 /tmp/pull-hp-metrics.sh.orig-task0434）
- 数据：去重 1,072,091+8,662 行，UNIQUE(timestamp,server) 索引，VACUUM 340MB→0.83MB
- 备份：/root/metrics.db.bak-task0434-20260821（340MB，观察 24h 稳定后可删）
- 未动：server.js、cron、HP 侧文件、服务进程（agent-dashboard 全程未重启）
- 旁路发现（供主 agent 知悉，非本任务范围）：HP 直报通道（collect-metrics.sh POST /api/metrics/ingest）12:05Z 后疑似断流/重试补发，pull 通道已独立覆盖每分钟数据，监控无缺口；属 task-0433 改动面
