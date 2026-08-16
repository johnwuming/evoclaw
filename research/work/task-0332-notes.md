# task-0332 清理笔记 — 老旧板块（模型进化僵尸版块 + 微盘股 Phase + 旧进化 API）

- 项目：/root/.openclaw/workspace/tools/agent-dashboard/server.js（655206 bytes，单文件）
- 备份：server.js.bak-task0332-20260817-002031
- 日期：2026-08-17 00:20 GMT+8

## 一、排查清单（grep 全量核实）

### A. 前端可见的僵尸版块
| # | 位置 | 内容 | 调用情况 | 决策 |
|---|---|---|---|---|
| A1 | L11418-11427 `loadEvolutionQuant` | 旧「模型进化」Tab 加载器（挂 `quant-page-evolution`） | **零引用**（导航只有 数据/因子/模型/回测·生命周期/模拟实盘，无 evolution 项；`quant-page-evolution` div 不存在） | 整体删除 |
| A2 | L11433-11450 `renderEvolutionQuant` | 旧进化页渲染（注释自认「兼容保留」） | 仅被 A1 调用 | 整体删除 |
| A3 | L9332-9391 `renderEvolutionHistory` | 「生命周期·进化历史」区块：旧三门禁（年化/回撤/Calmar）+ 旧进化汇总表 | 被「模型」页 L9799 引用一次；数据源 `/api/quant/evolution/summary` 读 `results/evolution-summary.json`——**该文件已不存在**（API 返回 empty → 页面只显示"暂无进化数据"占位）；新周期由 M2.5 决策时间线（decision-log.jsonl）+ M2.9 试验台账 + Tab4 迭代轨迹散点承载 | **下线该区块**（删函数+删调用）：新周期已有三处替代视图，改写耦合旧 evoSummary 结构成本更高 |
| A4 | L3650 `btlcResolveLayers` | 硬编码 fallback `'V2_d25_n30_p10'` 显示为选股基线版本 | 磁盘 sota.json 仍是旧值时会原样透出，fallback 更是永久硬编码 | 删除硬编码 fallback，改为仅在有 sota.version 时拼接 |

### B. 仅 API 死代码（后端路由，前端零调用已核实）
| # | 路由 | 位置 | 决策 |
|---|---|---|---|
| B1 | `/api/quant/evolution` | L1887 | deprecated stub `{ok:true,deprecated:true,note:...}` |
| B2 | `/api/quant/evolution/summary` | L3183 | 同上（A3 下线后零调用） |
| B3 | `/api/quant/microcap/status` | L2781 | deprecated stub |
| B4 | `/api/quant/microcap/phases` | L2793 | deprecated stub |
| B5 | `/api/quant/summary` ` /nav` ` /factors` | L1832/1853/1873 | 同批 deprecated stub（注释本就声明"不再被前端调用"；且 `KEEP_OLD_DATA_ARCHIVED=false` 会把 R-186/R-188 时代旧文件原样吐给任何调用方，违背注释意图） |

**保留** `/api/quant/evolution/models`（L3190）：读 model/main.json + sota.json + history.jsonl，**仍被「模型」页（L9300）与「模拟实盘」页（L11051）消费**（选股模型卡 main/SOTA、paper 模型版本）。history.jsonl 已含新周期 activate 记录（2026-08-16 task-0325/0327），非死数据。

### C. 微盘股 Phase 后端配套（随 B3/B4 一并删）
- `MICROCAP_STRATEGY`（L2668，含 `model: 'LightGBM + RD-Agent 因子进化'` 文案）
- `R196_PHASES`（L2703，Phase1-4 × 25 项旧路线检查表）
- `checkItemDone`（L2751）、`computeMicrocapPhases`（L2763）
- 死 CSS：`.microcap-param-*` `.microcap-phase-*` `.microcap-iter-*` 块（L6269-6293）+ L6352 复合选择器中的 `.microcap-param-value` 段

### D. 注释/文案
| # | 位置 | 处理 |
|---|---|---|
| D1 | L1795-1812 量化 API 头注释（"当前策略为微盘股 LightGBM+RD-Agent…Phase 2 进行中"） | 重写为新周期事实一句话 + deprecated 说明 |
| D2 | `KEEP_OLD_DATA_ARCHIVED` 常量（L1813-1815） | 随 B5 删除 |
| D3 | L8375-8376 「微盘股策略子视图…已移除/隐藏」注释 | 保留（已是新事实，无误导） |

## 二、保护清单核对（不动）
新量化 Tab 全模块（基线卡/五门禁/DSR/A-B-C对照/因子表/版本切换器/生命周期/迭代轨迹/管线/A2管线/freshness）、e2e 趋势、灰卡、报告详情、任务中心、paper 展示层、`/api/quant/baseline/*` `models` `lifecycle` `gates` `freshness` `q4b-contrast` `dsr` `registry` `decisions` `pending` `ideas` `ledger` `timing*` `paper/*` `btlc` `reports` — 均未触碰。

## 三、执行记录
- [x] 备份 server.js.bak-task0332-20260817-002031
- [x] A1-A4 前端删除/修正（含模型页 SOTA 徽章移除、btlc ②层版本不再回退 sota.json）
- [x] B1-B5 API stub 化（quantDeprecated 统一返回）
- [x] C 微盘股后端 + 死 CSS 删除
- [x] D1/D2 注释更新
- [x] node --check + restart + active
- [x] 回归：7 个新 API 全 200；根页 grep V2_d25=0；deprecated 路由返回标记
- [x] CDP 截图 /tmp/task0332-{quant,model,mobile}.png

## 四、验证证据（2026-08-17 00:39）
1. `node --check server.js` ✅；`systemctl is-active agent-dashboard` = active ✅
2. `curl -s http://127.0.0.1:8055/ | grep -c 'V2_d25_n30_p10'` = **0** ✅
3. 新周期 API：baseline/summary:200 models:200 lifecycle:200 gates:200 freshness:200 q4b-contrast:200 dsr:200 ✅
4. `/api/quant/microcap/phases`、`/api/quant/evolution`、`/api/quant/evolution/summary`、`/api/quant/summary|nav|factors`、`/api/quant/microcap/status` → `{ok:true,deprecated:true,note:'旧周期留档（微盘股 LightGBM+RD-Agent 路线，task-0250 废弃），2026-08-16 起新周期为 registry 驱动，2026-08-17 task-0332 清理'}` ✅（决策：保留路由返回 deprecated，未删）
5. `/api/quant/evolution/models` 保留且正常（返回新周期 main=v2b_trr）✅
6. CDP 双视口截图：/tmp/task0332-quant.png（153KB，因子页 107 因子表正常）/tmp/task0332-model.png（132KB，当前生效卡 v2b_trr + 决策时间线 + 试验台账正常）/tmp/task0332-mobile.png（181KB，390×844 导航 5 个子Tab 正常）✅
7. 全量子Tab渲染探针：data/factor/models/btlc/paper 全部 loadFail=false、v2d25=false、console 0 错误 ✅
8. 追加发现并同批清理：
   - 模型页「· SOTA V2_d25_n30_p10」徽章（读 sota.json 旧值）→ 移除（现役以 registry active 卡为准）
   - btlc 四层归因 ②基线层版本回退 sota.json 旧值 → 改为 registry version_id
   - `/api/quant/btlc` JSON 中 versions[].code_ref 仍含 `legacy(task-0272 upgrade from V2_d25_n30_p10)` 字样——这是 registry 版本文件的**代码来源描述**（历史事实记录，v1.1-v1.4 确从该版本引导而来），前端不渲染该字段，**保留不改**
9. 页面导航无死链：量化 Tab 5 个子Tab（数据/因子/模型/回测·生命周期/模拟实盘）均可切换渲染；主屏路由 `#page=quant` 正常

## 五、改动统计
- server.js: 655206 → 596704 bytes（约 -59KB：删除旧路由逻辑/微盘股静态配置/R196任务表/死CSS/僵尸前端函数）
- 全部残留 grep：`renderEvolutionQuant|loadEvolutionQuant|renderEvolutionHistory|evoSummary|quant-page-evolution|microcap-param|microcap-phase|microcap-iter` = 0 命中
- `微盘股|RD-Agent|LightGBM` 仅剩 5 处归档注释（deprecated 说明+历史事实），无 UI 可见残留
