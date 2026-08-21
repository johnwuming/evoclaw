# task-0439 监控口径修正 过程笔记

目标：CPU 采样窗 1s→5s；新增 cpu_cores / load_norm_1 双写；展示端归一化负载 + 口径标注；双端落地。

## 实查结论（0:50-0:55）
- collect-metrics.sh：/proc/stat 两次采样 sleep 1；loadavg_1 直接入库；无核数。INSERT 列清单 11 列。
- pull-hp-metrics.sh：INSERT OR IGNORE ... SELECT 列清单 11 列（sqlite3 与 node 两分支同）。
- server.js：
  - L236 建表 + L253 insertSystemMetric（named params）
  - L5412 METRIC_FIELDS（ingest 白名单 + 聚合列 + 密封缓存字段全集，加字段即全链路透传）
  - L5476 smRound：loadavg_1→2位；需加 load_norm_1→2、cpu_cores→0
  - L7185 USAGE_SYSMON_HTML 卡；L13555 smCard CPU/负载行；L13608 图4负载
  - /api/metrics/system/current 用 SELECT *，新列自动带出
  - /api/metrics/ingest 按 METRIC_FIELDS 白名单收数 → 加字段后 HP POST 上报也能带新列
- 关键链路：HP 数据到 VPS 有两条路：①HP cron POST ingest ②pull 每2分钟 INSERT OR IGNORE。若只改 pull 不改 ingest，先到的 POST 行无新列且 OR IGNORE 不会补 → 必须 server.js 同步改。

## 执行步骤
