# task-0498 / R-320 过程笔记（量化系统与 Dashboard 抽象合并精简方案）

> 边查边写：每完成一个取证点立即追加。恢复点文件。

## 时间线
- 2026-08-27 01:10 任务启动

## 0. 基础事实
- server.js: 825KB / 14942 行（任务书给定，待复核）
- 目标：纯方案设计，零代码改动
- 交付：R-320 报告 + 本笔记 + README 更新日志

## 取证计划
1. server.js API 端点全量提取（grep app.get/app.post）
2. 前端调用对照（grep fetch/axios 调用模式）
3. deprecated/legacy 标记定位
4. paper 双端点验证
5. 前端量化Tab 模块结构
6. HP 主机脚本与 crontab 清单（SSH 只读）

## 1. API 端点盘点（2026-08-27 01:15 取证）

**总量确认**：`grep -n "app\.(get|post|put|delete)(" server.js | grep -i quant | wc -l` = **60** ✓（与任务书一致）
全量清单落盘：/tmp/r320_quant_endpoints.txt

**前端调用机制**：前端内嵌于 server.js，统一走 `api('quant/xxx')` helper（L7532：`fetch(API + '/api/' + p)`），另有 post() 包装 POST /api/quant/action。

### 已确认 deprecated（quantDeprecated，L1850 定义，task-0332，共 7 个端点）：
1. /api/quant/summary (L1854)
2. /api/quant/nav (L1855)
3. /api/quant/factors (L1856)
4. /api/quant/evolution (L1857)
5. /api/quant/microcap/status (L2684)
6. /api/quant/microcap/phases (L2685)
7. /api/quant/evolution/summary (L3581)
（grep -c "quantDeprecated(res)" = 8 含函数定义行，实际 7 端点）

### 前端零调用端点（grep api('quant/<ep>') = 0 且全文引用=1 即仅自身定义）：
8. /api/quant/paper-summary (L2036) — 旧 paper 端点
9. /api/quant/paper-nav (L2053)
10. /api/quant/paper-trades (L2077)
11. /api/quant/paper-portfolio (L2106)
12. /api/quant/baseline/nav (L2772) — 引用=1
13. /api/quant/baseline/yearly (L2794) — 引用=1
14. /api/quant/endtoend (L4190) — 385 行大 handler，读 TIMING_ITER3_* CSV；引用=1 仅定义；前端改用 e2e-curves
15. /api/quant/engines/shadow-nav (L3800) — flat 兼容别名，api() 调用=0（引用 2 = 定义 + L13559 注释）；前端实际用 engines/:id/shadow-nav（L9771/13184 动态拼接）

### 双轨并存（新旧 paper 端点对，旧=零调用）：
- paper-summary (L2036) vs paper/summary (L3626) — 前端用后者 ✓
- paper-nav (L2053) vs paper/nav (L3658) — 前端用后者 ✓
- paper-trades (L2077) vs paper/trades (L3911) — 前端用后者 ✓
- paper-portfolio (L2106) vs paper/portfolio (L3943) — 前端用后者 ✓

### 前端实际调用（api('quant/...') grep，≥1 次）：~45 个端点
含动态拼接：engines/:id/shadow-nav、engines/:id/paper、history/:id、reports/:id
POST：action（写操作统一队列，L11668 注释）

**结论（初步）**：60 端点中 15 个零前端调用（7 deprecated + 8 死端点）= 25% 可删。
