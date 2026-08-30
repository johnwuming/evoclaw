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


## 现状确认（00:47）
### ① 手写字面位置
- perf-history.js activeEntry: `label: perf.label ?? 'vC-0 现役（权威·等波动率 58/42）'`
- **performance.json 无 label 字段**（实测 label=None）→ 线上实际输出的正是旧 fallback，含 task-0590 已撤销的「权威」字样，与 policy.json 矛盾。改动必要性强。
- policy.json（/root/.openclaw/workspace/tools/quant-dashboard/policy.json，3090B）caliber.display_name = "设计口径·提案轨迹（静态 58/42 月度再平衡·无风控层）"（08-30 task-0590 版本，已无权威字样）
- BFF src 现无任何 policy.json 引用；config.js 需加 policyPath（env POLICY_FILE 可覆盖，默认 ../../quant-dashboard/policy.json）
- 派生方案：perf.label 缺失 → 读 policy.caliber.display_name → 仍缺则降级 portfolio_version_id（禁手写字面）
### ② policy-lint 现状
- ⑤d 现有：Candidates.jsx/Version.jsx 断言无「权威口径（等波动率」字面 + 必须引用 rolling_compare/display_name
- 需扩：旧字面清单加入「vC-0 现役（权威·等波动率 58/42）」，扫 BFF src/*.js（口径相关源码）
### systemd 实况
- LEDGER_DIR=/root/.openclaw/workspace/tools/quant-bff/live（dataDir=live/data）
- ReadWritePaths 仅 state（BFF 零写面，读 policy.json 无碍）
