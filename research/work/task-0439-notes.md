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

## 落地记录
- VPS metrics.db ALTER 加列成功（sqlite3，列12/13：cpu_cores/load_norm_1）；旧数据 NULL 正常。
- collect-metrics.sh：sleep 5（实测总耗时 5.1-5.3s <10s cron 兼容）；cpu_cores（nproc 兜底 getconf/awk）；load_norm_1=loadavg/cores（%.3f）；INSERT/建表加新列；迁移 ALTER 幂等前置（sqlite3 分支 `2>/dev/null||true`，node 分支 try/catch）；hp 模式 POST body 加新字段。
- pull-hp-metrics.sh：4 处列清单（sqlite3/node 两分支 INSERT+SELECT）加 cpu_cores,load_norm_1。
- HP 侧：旧脚本备份 collect-metrics.sh.bak-task0439；HP metrics.db node:sqlite ALTER 成功；新脚本 scp+chmod。HP 实测 nproc=4（非任务书里写的16核，以机器实测为准），load 1.06 → norm 0.265。
- server.js：
  - 建表 SQL+insertSystemMetric 加列；启动幂等 ALTER 迁移（自愈）
  - METRIC_FIELDS 加 cpu_cores/load_norm_1（ingest 白名单+聚合列+密封缓存+趋势输出全链路生效——关键：HP cron 每分钟 POST ingest，若不改白名单，先到的 POST 行无新列且 pull 的 OR IGNORE 不会回补）
  - smRound：load_norm_1→2位，cpu_cores→0位
  - 前端：CPU 图题/CPU 卡行标「全核平均（5s 窗）」；负载图题改「loadavg 1m ÷ 核数，1.0=满载」；负载卡行显示归一值（回退原始），原始值进 title 悬停；图4 smLoadSeries（load_norm_1 优先，旧行折算 loadavg/cores）+ 满载 1.0 红虚线（全部服务器核数已知时）
  - node --check 通过；agent-dashboard.service 已重启，active
- 接口验证：/api/metrics/system/current 返回 cpu_cores=2(vps)/4(hp) 与 load_norm_1；趋势接口 5 分钟桶新桶已带 load_norm_1/cpu_cores（旧桶 NULL）。

## 口径对照（验收数字）
- CPU：同刻 top -bn2 -d5（第2轮=5s平均）42.1% idle ⇒ 57.9% busy；脚本 5s 窗读数 57.7% → 差 0.2pp（±10pp 内✓）。旧 1s 口径同场景读 95-100（单核峰值）。
- 负载：vps loadavg_1=5.53、cores=2 → norm 2.765（确实过载，红得有依据）；hp loadavg_1=1.06、cores=4 → norm 0.265（旧口径 1.06 在两台机器上不可比，归一后可比）。
