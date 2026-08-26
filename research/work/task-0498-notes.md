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

## 2. 前端模块结构（01:20 取证）

**量化Tab 实际 6 个子Tab**（_V5_TABS L9468：data/factor/v5model/v5btlc/paper/v5hist），UI 按钮 L7408-7413：
数据 | 因子 | 回测 | 模拟实盘·灰度 | 迭代历史（+因子默认）

**孤儿 div（死 UI）**：`quant-page-models`（L7425）、`quant-page-btlc`（L7426）——不在 _V5_TABS、无对应 qseg 按钮、无 renderer 写入（grep 引用=仅自身定义行）→ 纯死代码，删除证据确凿。

**各 loader 行区间（估模块体量）**：
- loadV5ModelQuant L9658-9755（模型，98 行）
- loadV5BtlcQuant L9756-10409（回测·生命周期，653 行，含 F6 模块 L10008 起=R-319、e2e-curves、timing-matrix、q4b-contrast L12735 附近实际在 factor 段）
- loadV5HistQuant L10410-10602（迭代历史，193 行）
- loadDataQuant L10603-10749（数据，147 行）
- loadFactorQuant L10750-13151（因子，~2400 行，最大段：因子目录/IC/corr/择时）
- loadPaperQuant L13152-13800+（模拟实盘，engines+shadow-nav+paper 实时，R-313/R-315）

**顶栏横件**：quantConsistDot 一致性自检（task-0359，consistency API）、quantFreshness 新鲜度。

## 3. 关键定位复核
- L2863-2866：q4b-contrast 的 A/B 存活池 legacy 标签（q4b-contrast 前端在用 L12735，属 factor 段）→ 不是死代码，但 A/BUB legacy 口径可讨论退役
- L3378 quantIsLegacyVersion：在役（task-0359），判定 v0_/v1 系为旧周期，渲染时灰显
- TIMING_ITER3 常量 3 个（L4126-4128）仅被 endtoend（L4190）使用 → endtoend 删则常量随删
