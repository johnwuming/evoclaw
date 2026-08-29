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
