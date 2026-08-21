# task-0433 过程笔记：恢复 sysmon 卡 + 修复 /api/metrics/system 性能

## 实查发现（DB 只读，未做任何写操作）

- metrics.db 340MB + WAL 262MB；表 `system_metrics(id,timestamp,server,cpu_pct,mem_used_pct,mem_total_mb,disk_used_pct,disk_total_gb,net_rx_kbps,net_tx_kbps,temp_c,loadavg_1)`，索引 `(server,timestamp)`、`(timestamp)`。
- **timestamp 格式严格统一为 20 字符 `YYYY-MM-DDTHH:MM:SSZ`**（无毫秒，COUNT len≠20 = 0）→ substr 定位分钟安全。
- 24h 窗口行数：**hp=1,156,786（均值 ~13.4 行/秒）**，vps=2,139（~40s 一条）。
- HP 按小时密度呈衰减：08-21T00 时 20,494 条/时（5.7/s）→ 11 时 704 条/时（≈1/min），尾部写入已恢复 1/min。历史突发密度是 115MB 响应根因；DB 有 24h 滚动 prune（每小时），旧密度会自然滚出。
- 修前接口：`SELECT * ... WHERE server=? AND timestamp>=?` 全量返回 → 8.6s / 115.9MB（上轮实测）。

## 性能实验（read-only 连接实测）

- strftime 分钟桶 GROUP BY（hp，24h）：CLI 2.57s；node:sqlite 3.6s。
- substr 纯字符串桶替代 strftime：2.3~4.0s——瓶颈不在表达式，在 116 万行索引→表逐行取列。**纯全量聚合无法 <1s。**
- 结论：采用 **5 分钟桶 SQL 聚合 + 密封桶（sealed bucket）增量缓存 + 响应 30s 缓存**：
  - 历史完整桶只聚合一次进内存（SUM/COUNT 精确累加）；
  - 每次请求只重扫最近 ~15 分钟原始行（当前密度 ~5k 行，<50ms）；
  - 响应按 (server,hours,gran) 缓存 30s，带 Age 头。
- 桶粒度选择：5min → 24h=288 点/服务器，与前端 smDownsample 每序列 300 点上限对齐（前端零二次抽样、零改动）。
- 响应体积估算：288×2 行 × ~200B ≈ 120-160KB < 200KB 目标。
- 密封边界留 2 桶（10min）滞后余量容忍迟到样本；>10min 迟到样本不入聚合（HP 推送间隔 1min，可接受）。

## 实施内容（最终）

1. 后端 `/api/metrics/system` 重写（server.js，git 5f93320）：
   - 5 分钟桶 GROUP BY（SUM/COUNT 精确累加，输出均值，保留 1-2 位小数）；可选 `gran=1/2/5/10/15/30/60` 参数（非 5 时走全量扫描路径）；hours>48 默认 30min 桶。
   - 密封桶增量缓存：完整历史桶只算一次，每次请求只重扫最近 ~10 分钟；启动后台分片预热（1h/片 + setImmediate 让出），启动窗口请求实测 <0.1s 且数据完整。
   - 响应级 30s 缓存（Age 头）+ X-Downsample-Bucket-Min 头；数据形状不变。
   - 开发中修过一个 bug：首次构建曾只扫密封边界后数据（返回 876B），已改为 fullBuild 时从 buildFrom 全量扫描。
2. 前端：USAGE_CARDS 恢复 sysmon（volc/hp 维持注释）；showPage('usage') 恢复 loadSystemMetrics()；_sysMonDisabled=false（30s 轮询恢复，保留应急开关）。
3. metrics.db：零写操作；服务重启未动 prune/ingest 行为。

## 验证结果（全部实测）

- node --check ✓；服务 active（重启多次，当前正常运行）
- **性能前后对比（主验收项）**：
  - 修前：8.6s / 115.9MB（上轮实测，SELECT * 全量）
  - 修后稳态（TTL 过期增量重建）：**0.034s / 113.9KB**（288 点/服务器，覆盖完整 24h）
  - 响应缓存命中：0.003-0.02s；重启后启动窗口首次请求：0.10s（分片预热生效，数据完整）
  - 冷全量扫描（无预热理论上限）：~11-13s，仅发生在预热被旁路时，用户路径不可达
- 聚合正确性抽验：hp 2026-08-21T06:00 桶 API 值 cpu=28.6/load=1.08 与 SQL 直查 AVG 精确一致（无重复计数）
- 页面：GET / 200；USAGE_CARDS 实际返回四卡 zhipu/volcCoding/deepseek/sysmon（sysmon 行生效）；volc/hp 行维持注释；_sysMonDisabled=false；loadSystemMetrics() 调用恢复
- git：单 commit 5f93320，仅 server.js（155+/10-），无无关文件（untracked 的 db/bak/png 均未提交）
- .task-completions.jsonl 已写入

## 遗留发现（建议后续任务，本轮按约束未动）

1. **pruneSystemMetrics 从未生效**（pre-existing）：`metricsDb.run is not a function`（node:sqlite DatabaseSync 无裸 .run），24h 滚动清理自迁移以来一直报错，DB 无限膨胀至 340MB+WAL 262MB。修复≈一行（改 prepare().run()），但修复后首次重启会触发 117 万行 DELETE（分钟级阻塞+WAL 膨胀），需与 WAL checkpoint/vacuum 瘦身一起规划。
2. HP 采集端疑似补发旧时间戳数据（~10 行/秒夹杂旧 ts），密封桶设计对 >10min 迟到样本不回补（趋势图历史段均值基于当时已到数据，当前实时段准确）；修好 prune+HP 采集节奏后此问题自然消失。
