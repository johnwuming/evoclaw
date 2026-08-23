# task-0476 notes 2026-08-24 00:27:10

## 2026-08-24 01:20 主 agent 接管完成（子 agent 空转 33min 零产出）
- 根因（主 agent 诊断）：smWarmSlices 预热只折叠到重启前 ~10min 桶；smAggServer 增量路径每次只扫最近 10min（scanFrom=sealFromIso）；服务重启后若看板未持续刷新，中间段桶永不折叠进密封缓存 → API 缺口 420min（db 数据完整未丢）。
- 修复两处（git commit bc6307b）：
  1. pruneSystemMetrics L268: `metricsDb.run(...)` → `metricsDb.prepare('DELETE...').run(cutoff)`（node:sqlite DatabaseSync 无 .run()，原一直报 run is not a function）
  2. smAggServer 增量路径缺口自愈：遍历 st.buckets 找 maxKey，若落后 sealFromIso 超 3 桶（>15min）→ 从 buildFromIso 全量重扫折叠（fullBuild=true），确保重启后历史桶全部进缓存
- 验证：node --check OK；systemctl restart 后 /api/metrics/system?server=vps&hours=24 实测 287 点、0 缺口（>10min 阈值）；新进程启动后无 prune 报错（旧进程 01:17:51 那条是重启前）
