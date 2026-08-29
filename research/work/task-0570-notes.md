# task-0570 修订笔记（2026-08-30）

## 对象与版本
1. R-342 v1.3→v2.0：BFF 全量端点契约收编（以 src/app.js 实际注册为准）+ 数据流 + 构建规约
2. R-344 v1.2→v1.3：R-359 43 模块对照表附录收编
3. R-336 附录A：GLOSSARY 术语表
4. spawn-task.md：Dashboard 开发附加纪律段

## 文件大小（wc -c）
- R-342: 46301（>30KB 禁全读，分段取）
- R-344: 26618（分段读）
- R-336: 59996（>30KB 禁全读）
- spawn-task.md: 6306（可全读）
- R-359 审计: 14535（可全读）

## 结构发现
- R-342：§3.4 前端 API 契约（L198-217）、修订记录 L386、契约与现实对齐段 L393 起

## 关键发现（2026-08-30）
- BFF 项目：/root/.openclaw/workspace/tools/quant-bff/（systemd quant-bff.service，PORT=8180，127.0.0.1）
- 入口 server.js → 应用工厂 createApp 在 src/app.js（19609B，已全读）
- apiPrefix 由 config.js 提供（待确认，预期 /api/v1）

## app.js 实际注册端点全集（L379-396，唯一事实源）
全部 GET；apiPrefix 记为 ${p}：
1. ${p}/health — healthHandler
2. ${p}/events — ledgerDerived(eventsHandler)
3. ${p}/migration — 独立文件源（data/migration.json），不随账本 503
4. ${p}/overview — ledgerDerived(overviewHandler)
5. ${p}/engines — ledgerDerived（data/engines.json）
6. ${p}/portfolios — ledgerDerived（data/portfolios.json，?status=&limit=）
7. ${p}/portfolios/:id — ledgerDerived（data/versions/<id>.json + performance 扩展 W4.5）
8. ${p}/portfolios/:id/holdings — ledgerDerived（trade.fill 读时投影，W7/task-0557）
9. ${p}/portfolios/:id/trades — ledgerDerived（trade.fill 投影+fee 汇总，W7）
10. ${p}/portfolios/:id/navseries — 独立镜像文件源（W8/task-0560，缺失降级 null）
11. ${p}/risk/gates — ledgerDerived（assembleRiskGates，W5）
12. ${p}/perf-history — perfHistoryHandler（独立文件源，W6/task-0555）
13. ${p}/perf-history/:id — perfHistoryDetailHandler（缺失降级 null）
兜底：${p} 下未实现→404 NOT_IMPLEMENTED_THIS_BATCH；全局→404 NOT_FOUND；错误中间件 {error:{code,message}}
横切：requestTimeout 5s → 503 UPSTREAM_TIMEOUT；ledgerDerived 门卫 → 503 INITIALIZING/LEDGER_CORRUPTED/PROJECTION_MISMATCH/LEDGER_REFRESH_TIMEOUT
未实现（R-342 §3.4 原承诺、R-359 B1/B2）：risk/drift、portfolios/:id/timeline → 404 NOT_IMPLEMENTED_THIS_BATCH

## 前端项目（quant-dashboard，dashv6）
- 路径 /root/.openclaw/workspace/tools/quant-dashboard/，Vite+React18，base=/quantv6/
- dev 5173 / preview 4173，proxy /api → 127.0.0.1:8180（quant-bff）
- src/api.js L4：API_BASE=(import.meta.env.VITE_API_BASE||'').replace(/\/$/,'')；生产 VITE_API_BASE=/quantv6 → 请求 /quantv6/api/v1/*（nginx 映射回 BFF /api/*）
- fmtID(id,max=14) 在 api.js L97；Events.jsx actor/target 过滤已有（E3 已补）

## risk/gates 完整返回（assembleRiskGates，schema risk_gates@v2）
{schema, run_date, circuit_breaker{state,reason}, drift{run_date,source_file,dims[]}, recon{run_date,source_file,...摘要}, pending_risks{count,items}, portfolio_dd_gate{drawdown_pct,peak_nav,peak_date,as_of,band,action,caliber,band_source,charter{cut_half_at,stop_at,charter_version},status,note}, vol{target,band_pp,window_days,realized,obs_count,in_band,status,note}, correlation{pair,method,window_days,corr,corr_prev_5d,flag_level,flag_label,thresholds{t1:0.75,t2:0.85,t3:0.9},status,note}}

## 其他端点关键结构
- portfolios/:id/navseries：schema nav_series@v1，{portfolio_version_id,status,caliber:runtime_paper,source,nav_series,summary{nav,nav_chg_1d,nav_chg_1d_pct,mdd,drawdown_pct,data_start,data_end,points}}；非 paper→note 引 /perf-history/:id；缺失降级 null
- perf-history：schema perf_history@v1 {generated_at,caliber_ref,versions[],skipped[]}；:id → perf_history_detail@v1 {performance|null（nav_curve）}；vC-0 特判
- health 增量字段：ready,status,reconciliation_ok,ledger_corrupted,replay_duration_ms,replay_mode,replay_events,ledger_errors,cold_archive{files,events,min_ts,max_ts}
- events：X-Ledger-Tail-Ts 响应头；cursor=`<ordinal>:<ts>`；type 支持 promotion.* 前缀通配；payload>400B 截断为 summary
