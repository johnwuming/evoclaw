# task-0592 过程笔记（2026-08-31 00:45 开始）

任务：BFF 维护窗口合批开发四项
① perf-history.js fallback 手写字面 label 清除 → 从 policy.json 派生
② policy-lint.mjs 扩扫 BFF 源码
③ candidates 徽标 computed height 断言
④ lint 输出附扫描面清单

## 文件清单确认（00:45）
- /root/.openclaw/workspace/tools/quant-bff/src/perf-history.js = 6202 bytes（可全读）
- /root/.openclaw/workspace/tools/quant-dashboard/scripts/policy-lint.mjs = 24382 bytes（<30KB 可全读）
- BFF src 其他文件：app.js 22340 / config.js 2128 / ctx.js 6046 / ledger.js 10097 / nav-series.js 4971 / pending-risks.js 2258 / replay.js 8213 / risk-gates.js 13892 / server.js 1712

