# task-0498 / R-320 过程笔记（原始证据堆）

时间：2026-08-27 01:42 GMT+8 起。任务：量化系统与 Dashboard 抽象合并精简方案设计（零代码改动）。

## E1. Dashboard 仓库结构（VPS）

- 路径：/root/.openclaw/workspace/tools/agent-dashboard/
- server.js：825KB 单体（后端路由 + 前端 HTML/JS 全部内嵌，`res.send(\`<!DOCTYPE...) 未直接命中，HTML 以模板字符串内嵌于 server.js）
- public/：仅 vendor 静态库（chart.umd.min.js、marked.min.js、remixicon）
- scripts/：collect-metrics.sh、pull-hp-metrics.sh（VPS 每 2 分钟从 HP metrics.db 增量拉取，watermark 机制，2026-08-21 task-0434 重构）
- 备份文件：server.js.bak-* 共 40+ 个堆在仓库根目录（卫生问题）
- db：dashboard.db、metrics.db（含 hp 服务器行）、tasks.db

## E2. 后端量化 API 端点（grep server.js 全量，60 个）

deprecated 网关 quantDeprecated（task-0332 旧周期留档）：
- /api/quant/summary, /nav, /factors, /evolution（1854-1857）
- /api/quant/microcap/status, /microcap/phases（2684-2685）
- /api/quant/evolution/summary（3581）

活跃端点（行号见 /tmp/quant-endpoints.txt）：
factor-catalog 1990, factor-ic-series 2006, paper-summary 2036, paper-nav 2053, paper-trades 2077, paper-portfolio 2106, reports 2143, reports/:id 2171, timing 2214, data-health 2237, data-assets 2264, timing-config 2417, registry 2431, decisions 2448, pending 2471, ideas 2525, ledger 2543, lifecycle 2574, baseline/summary 2756, baseline/nav 2772, baseline/yearly 2794, baseline/meta 2818, q4b-contrast 2870, gates 2915, dsr 2943, models 2959, active 3230, active/pos 3240, active/curves 3277, version-options 3318, history 3384, history/:versionId 3441, freshness 3477, consistency 3535, evolution/models 3583, paper/summary 3626, paper/nav 3658, engines 3681, engines/:id/shadow-nav 3756, engines/shadow-nav 3800, engines/:id/paper 3809, paper/trades 3911, paper/portfolio 3943, run-status 3962, crowding 3987, risk-status 4032, action(POST) 4053, action-queue 4104, endtoend 4190, btlc 4575, e2e-curves 4689, f6-curves 4798, timing-matrix 4891

## E3. 前端量化 Tab 结构

- quantTabMode 默认 'factor'，五个子 Tab：数据 | 因子 | 模型 | 回测·生命周期 | 模拟实盘（task-0280 起，server.js:9377）
- localStorage quantTab 持久化
