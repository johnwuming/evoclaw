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

## 实施内容

1. 后端 L5363 起 `/api/metrics/system` 重写（见 server.js diff）：
   - hours≤48 且无自定义粒度 → 增量路径（smAggServer）；
   - hours>48 或 gran 参数 → 全量 GROUP BY 路径（30min 桶 / 指定粒度），同样走 30s 响应缓存；
   - 数据形状保持 `{timestamp, cpu_pct, ...}`，前端 loadSystemMetrics 零改动。
2. 前端：
   - USAGE_CARDS 恢复 sysmon 行（volc/hp 维持注释）；
   - showPage('usage') 恢复 loadSystemMetrics() 调用（volc/hp 刷新维持移除）；
   - `_sysMonDisabled = false`（保留守卫作应急开关）。
3. metrics.db：零写操作（连接只读测试；服务自身 ingest/prune 行为未动）。

## 验证（待补，完成后填数字）

- [ ] node --check
- [ ] 服务重启 active
- [ ] curl 计时 /api/metrics/system?hours=24（冷/热/缓存命中）
- [ ] 响应体积
- [ ] 用量页 200 + sysmon 卡 HTML 存在 + volc/hp 卡不存在
- [ ] git 单 commit
