# R-366 风控闸门 Phase 1 实装（task-0565，T1+T2）

> 依据 R-362 §5–§7 契约，按 2026-08-29 18:16 用户批准决策点执行：D-1=c（相关性仅结构展示，不做 T3/T4/T5、不碰 HP）、D-2=a（BFF 镜像现算）、D-3=a（目标四带主显+宪章辅显）、D-4=20 交易日、D-5=corr(t)>corr(t−5)、D-6=不动 HP 挂点。

## 1. 交付摘要

| 项 | 内容 | 状态 |
|---|---|---|
| T1 BFF risk_gates@v2 | `schema` + `portfolio_dd_gate` + `vol` + `correlation` 三新块；旧键逐字不变 | ✅ 48/48 测试 + 线上 200 实测 |
| T2 前端三卡 | Risk.jsx 回撤四带仪表 + 波动率带 + 相关性结构，插断路器卡之后，置顶机制未动 | ✅ build + 390×844 无头验收 |
| 回退预案 | 还原本任务 5 个源文件 + `npm run build` + `systemctl restart quant-bff` 即回 v1；无数据面改动 | — |

## 2. T1 BFF 实现要点

- **改动文件**：`tools/quant-bff/src/risk-gates.js`（纯新增函数 + assemble 追加三块）、`src/config.js`（+`equityNavPath`/`goldShadowNavPath`，env `EQUITY_NAV_FILE`/`GOLD_SHADOW_NAV_FILE` 可覆盖，本阶段仅落配置位不读取）、`test/risk-gates.test.js`（新增 8 例）。
- **回撤四带**：`drawdown_pct = nav/peak − 1`（≤0，0=新高，4dp，按 §5 契约符号约定；§3.1 公式字面 `1−nav/max` 与「小数≤0」矛盾，以契约为准）；带边界 0.05/0.10/0.15 入高带（精确 5% 即 escalated_review）；`charter` 运行时读 `dataDir/versions/vC-0.json → risk_control.drawdown_gates.in_service_charter`，缺失/坏值回退 {0.25, 0.35, "1.0"}。
- **波动率带**：obs 口径 = NAV 观测数（20 交易日 = 20 个 NAV 点 → 19 个邻日收益算样本 std ×√252，4dp）。当前镜像 11 行 → **obs_count=11/20 insufficient_obs**，与 R-362 §3.1「现 11/20 属预期」一致；|realized−0.08|≤0.02 → in_band。
- **相关性（D-1=c）**：静态结构块，corr/corr_prev_5d/flag_level/flag_label 全 null + `status=insufficient_data`；thresholds {t1:0.75, t2:0.85, t3:0.90}；`corr_prev_5d` 即 D-5 上升判定参数位（note 注明口径）；pair=equity_sleeve_vs_hedge_sleeve_gold。
- **降级语义**：源缺失 → dd/vol 数值全 null + `unavailable`，响应仍 200；每新块带 `note=「看板展示口径，不构成风控动作依据」`。
- **测试**（`test/risk-gates.test.js`）：四带边界（4.99/5.01/10.01/15.01% 及精确边界）、峰值追踪/新高、vol 满窗 ok / insufficient_obs / unavailable、parseNavCsv 多列兼容+脏行、v2 集成（fixture NAV 注入：旧键结构+取值回归快照、charter 注入、源缺失降级）、correlationBlock 契约冻结。**48/48 全过（基线 33 + 新增）**。

## 3. 线上实测（systemctl restart quant-bff 后）

`GET /api/v1/risk/gates` = 200，实测（/tmp/t0565-gates.json）：

- `portfolio_dd_gate`: drawdown_pct=0（08-28 新高）、peak_nav=1.00993@2026-08-28、band=lt5、action=normal、charter 0.25/0.35/1.0 ✓
- `vol`: insufficient_obs、obs_count=11/20 ✓
- `correlation`: insufficient_data + 三档阈值 ✓
- 旧键完好：run_date=2026-08-28、circuit_breaker 未触发、drift 4 维、pending_risks 正常 ✓

## 4. T2 前端（Risk.jsx + styles.css）

- **回撤四带卡**：分段横条（绿/黄/橙/红 四段）+ 当前值游标（满刻度 15%）+ 数值区（当前回撤/峰值/截至）+ 宪章辅显小字「减半 ≥25% · 止损 ≥35% · v1.0」。
- **波动率带卡**：0–16% 刻度内 6–10% 目标带区间条 + realized 点位；insufficient 时「窗口积累中 11/20 交易日 · 目标带 6–10%（结构预置）」。
- **相关性卡**：三档阈值图例（0.75 观察筛查 / 0.85 且上升→防御减仓 / 0.90 升级复核）+ 上升判定 corr(t)>corr(t−5) + 「两腿日频序列就绪前不判带（insufficient_data）」。
- 每卡底部口径角标「看板展示口径，不构成风控动作依据」；降级灰显（rk-dim-na）+ 文案，无空白；零新依赖；单列堆叠、无固定宽 SVG、无超长字符串。
- **构建**：`VITE_API_BASE=/quantv6 npm run build` ✓（dist/assets/index-DV6y0eV7.js；nginx alias 直接伺服 dist，构建即上线）。
- **390×844 无头验收**（playwright + headless chromium）：`bodyScrollW=390`、`docScrollW=390`（无横向滚动）、三卡可见、vol 进度文案 11/20、宪章 25/35 均在 DOM 实测到；截图 `dist/screenshots/task-0565-risk-390.png`。

## 5. 纪律核验

- 零 crontab 接触、HP 零改动（D-6）、零新增数据产物：相关性/equity/gold 路径仅落 config 位，未新增任何文件读取之外的产物。
- 未修改与任务无关文件；quant-bff/、quant-dashboard/ 未纳入 git 跟踪（回退按 §1 预案手工还原）。
- 新增验收脚本 `tools/quant-dashboard/scripts/t0565-serve.cjs`、`t0565-headless-check.cjs` 供复跑（本地 8981 静态+反代，非生产组件）。

## 6. 遗留与后续

- T3/T4/T5 未做（D-1=c 范围外）：两腿日频产物、相关性点亮、sleeves_ddc、HP 权威对账文件待后续批准。
- vol 的 std 用样本口径（n−1）；满窗后首个实测值建议在报告中复核一次（约 2 周后 20/20）。
- 教训：验收脚本 `__dirname` 相对路径写错（scripts/dist vs dist）导致 404 假象，排障 ~10 分钟——一次性验收脚本也应先 `curl` 静态资源冒烟。

## 7. 来源

- R-362 §3–§8（契约与决策点）；notes：`work/task-0565-notes.md`；实测：`/tmp/t0565-gates.json`、无头检查输出（bodyScrollW=390，exit=0）。
