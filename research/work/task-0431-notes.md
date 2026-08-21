# task-0431 用量页卡片移除 + 根因诊断笔记

日期：2026-08-21 19:38–19:45 | 执行：subagent | 审核：主 agent

## 一、根因诊断（结论先行）

**用量页卡死的真凶是「服务器监控」(sysmon) 卡的 `/api/metrics/system?hours=24`：本地实测 8.6s 返回 115,897,670 字节（115MB）。**

逐端点实测（2026-08-21 19:39，curl -w，改前）：

| 端点 | 用途（卡） | http | 耗时 | 响应大小 |
|---|---|---|---|---|
| /api/zai-quota | 智谱 GLM | 200 | 2.1ms | 551B |
| /api/volc-quota | 火山 Agent Plan | 200 | 1.7ms | 357B |
| /api/volc-coding-quota | 火山 Coding Plan | 200 | 1.6ms | 481B |
| /api/deepseek-quota | DeepSeek | 200 | 3.4ms | 215B |
| /api/hp-stats | HP-800G1 | 200 | 0.77s | 295B |
| **/api/metrics/system?hours=24** | **服务器监控** | **200** | **8.60s** | **115.9MB** |
| /api/metrics/system/current | 服务器监控(当前值) | 200 | 0.19s | 457B |

### 为什么 metrics/system 会 115MB

server.js L5363-5381：`SELECT * FROM system_metrics WHERE server=? AND timestamp>=cutoff ORDER BY timestamp ASC` —— **无降采样、无 LIMIT、无缓存**，24h 原始采样全量回传（metrics.db 340MB + WAL 262MB）。前端 `loadSystemMetrics()`（L13416）用 `cache:'no-store'` 拉取后 JSON.parse 115MB，主线程冻结数秒；且 30s 定时器（L13436）+ visibilitychange（L13437-13441）在用量页可见期间反复拉取 → 页面持续卡顿/加载不出来。

### 其他端点为何快

- zai/volc/volcCoding/deepseek：后端有内存缓存 + 定时后台刷新（volc 5min 间隔 VOLC_QUOTA_INTERVAL_MS），前端只读缓存。
- hp-stats：SSH execFile 带 10s timeout（L1692 附近）+ 30s 服务端缓存（HP_CACHE_MS）+ in-flight 去重（等待最多 8s）。SSH 冷/坏时最坏 ~10s，但非本次主因。

### 判定：sysmon 一并移除

任务授权「sysmon 若是主因一并移除」——实测它就是主因（115MB/8.6s 远超其他所有端点之和），故三卡全去：volc（Agent Plan）+ hp + sysmon。

## 二、改动清单（git diff 共 3 处，+9/-6 行）

基线：`git init` 于 tools/agent-dashboard/，commit `1c7d420`（baseline before task-0431，含 server.js/package.json/package-lock.json；db/png/node_modules/秘密未入库——.volc-secrets.json 与 .session-secret 不在 commit 内）。

1. **USAGE_CARDS 数组**（L~13444）：注释掉 volc / hp / sysmon 三项（保留注释行，恢复=取消注释）。
2. **showPage('usage') 调用链**（L7036）：移除 `refreshVolcStatus()` / `refreshHpStatus()` / `loadSystemMetrics()` 三个调用；保留 refreshZaiStatus/refreshVolcCodingStatus/refreshDsStatus。
3. **sysmon 轮询开关**（L~13436）：新增 `var _sysMonDisabled = true;`，30s setInterval 与 visibilitychange 回调加 `!_sysMonDisabled` 守卫（否则卡片移除后仍每 30s 拉 115MB，白卡）。恢复 sysmon 卡时把它改回 false。

**函数体全部保留**：refreshVolcStatus/refreshHpStatus/loadSystemMetrics/renderSystemMetrics 等定义未动；refreshVolcQuotaNow/refreshHpNow（卡片内手动刷新按钮 handler）成死代码但保留，可恢复。

**localStorage 兼容**：normalizeUsageCardCfg（L~13464）的 known-map filter 会把旧 cfg 里已移除 key（volc/hp/sysmon）自动滤掉并回写，无报错路径（实读代码确认）。

## 三、验证记录

- `node --check server.js` → SYNTAX OK
- `systemctl restart agent-dashboard` → active；`/api/health` 200（97MB RSS）
- 用量页 `GET /` → 200，85ms
- 服务端 HTML 抓取确认：`name === 'usage') { buildUsageCards(); applyUsageCardCfg(); refreshZaiStatus(); refreshVolcCodingStatus(); refreshDsStatus(); }` —— usage 路径不再触发 volc/hp/sysmon 拉取
- 改后剩余用量页 API 复测：zai 1.7ms / volcCoding 4.0ms / deepseek 1.3ms
- `git diff --stat`：仅 server.js，15 行变更（3 处），无无关文件改动

## 四、留批的结构性优化建议（本次未实施）

1. **metrics/system 降采样**（治本）：SQL 按分钟 bucket 聚合（GROUP BY strftime('%Y-%m-%dT%H:%M')）或 LTTB 抽样，24h 数据从 ~87 万行压到 ~1.4k 点；或加 `?step=` 参数由前端控制粒度。
2. **加缓存/ETag**：该路由加 30-60s 内存缓存（对齐 hp-stats 的做法），no-store 改成 revalidate。
3. **metrics.db 瘦身**：340MB 主库 + 262MB WAL——定期 PRAGMA wal_checkpoint(TRUNCATE) + 原始数据保留窗口（如 >7d 降采样归档后删除）。
4. **hp-stats SSH 超时收窄**：10s timeout 可降到 5s；或改由 HP 侧 cron 主动 POST /api/metrics/ingest（该通道已存在），去掉 VPS→HP 的同步 SSH 等待。
5. **前端并行渲染**：6 个 refresh 若未来再加卡，建议 Promise.allSettled 而非各自 async（当前非阻塞主因，低优先级）。

## 五、备份/恢复

- git 基线：`cd tools/agent-dashboard && git log --oneline` → `1c7d420 baseline before task-0431...`；回滚 `git checkout -- server.js`（或 `git revert`）。
- 恢复三卡：取消 USAGE_CARDS 三行注释 + showPage 加回三个调用 + `_sysMonDisabled=false`（若不先修 115MB 问题，恢复 sysmon 后卡顿会复发）。
