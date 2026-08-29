# R-358 总览页 NAV 区块接入与运行态 NAV 同步通道（task-0560）

- 日期：2026-08-29 ｜ 类型：VPS 侧功能接入（HP 零改动） ｜ 执行：主会话 spawn 子代理
- 背景：总览页区块①「净值与回撤」长期空态（"NAV 数据待接入"）。运行态 NAV 数据本体已在 HP 产出并镜像到 VPS，本次打通「镜像 → BFF 端点 → 总览页渲染」最后一公里。

## 1. 同步通道（零 crontab 变更）

**结论：既有通道已完整覆盖运行态产物，未改任何同步脚本，未动 crontab。**

- 通道：`/root/.openclaw/workspace-quant/scripts/auto_sync_notify.py`，cron 每 30 分钟增量（`cron-auto-sync`）+ 每日 03:00 全量（任务书所述"每日 8:30"实为每 30 分钟，频率更高）。
- 覆盖证明：`MIRROR_INCLUDES` 中 `--include=baseline-paper-*`（task-0352 引入）已覆盖运行态四件套：
  - `baseline-paper-nav.csv`（header `date,nav`，HP 每交易日 16:30 后追加）
  - `baseline-paper-trades.csv` / `baseline-paper-portfolio.json` / `baseline-paper-summary.json`
- 命名澄清：任务书所写 HP 路径 `~/quant-evolve/results/paper-nav.csv` 实际不存在（HP 侧已核实 MISSING），真实文件名即 `baseline-paper-nav.csv`；口径为同一运行态序列。
- 手动触发：本次以 cron 同参数手动执行一次 `auto_sync_notify.py --job-name cron-auto-sync`，同步成功（synced_files:1）；镜像副本 `/root/.openclaw/workspace-quant/results/baseline-paper-nav.csv` 末行 `2026-08-28,1.00993`（8/29 周六无交易日，数据已最新）。下一交易日起每 30 分钟内自动增量，无需任何变更。

## 2. BFF 新端点：GET /api/v1/portfolios/:id/navseries

- 实现：`src/nav-series.js`（新文件）；`src/config.js` 新增 `paperNavPath`（默认 `/root/.openclaw/workspace-quant/results/baseline-paper-nav.csv`，env `PAPER_NAV_FILE` 可覆盖，测试注入 fixture）；`src/app.js` 注册路由（独立镜像文件源，`.catch(next)` 形态同 migration，不套 ledgerDerived——与账本无关，参照 perf-history 先例，不随账本 503）。
- 响应契约 `nav_series@v1`：`{ schema, portfolio_version_id, status, caliber:'runtime_paper', source:'mirror:<file>', nav_series:[{date,nav}], summary }`。
- summary 汇总：末值 `nav` / 日变动 `nav_chg_1d`（4dp 小数，与 /overview 同口径）/ `nav_chg_1d_pct`（百分数）/ `mdd`（负值）/ `drawdown_pct`（当前回撤距历史高点，负值，0=新高）/ `data_start` / `data_end` / `points`。
- 降级语义（均 200 不 503）：镜像文件缺失/空 → `nav_series:null, summary:null`（前端维持空态）；id 非法 → 400 `BAD_ID`；portfolios.json 无此 id → 404；非 paper 组合 → `series:null` + note 指向 `/perf-history/:id`（**运行态与回测口径不混源**）。
- CSV 解析按表头取 `date`/`nav` 列，容忍附加列（cash/holdings_value/total）。
- 零写路径；systemd unit 零改动（默认值即生产路径）；`npm test` 38/38 全过（基线 35 + 新增 `test/nav-series.test.js` 3 例：happy path / 缺失降级 / 400+404+非paper）。

## 3. 总览页区块①接入

- `src/api.js`：新增 `fetchNavSeries(id)`。
- `src/pages/Overview.jsx`：区块①空态桩替换为运行态 NAV 卡——SVG 轻量曲线（无依赖，同 Version.jsx NavChart 范式，viewBox 自适应）+ 口径标注「运行态 · 起始 2026-08-14」+ 30/90/1Y 切换（按数据量自适应，11 点全显）+ 四角标（末值/日变动/MDD/回撤）。数据拉取独立降级：navseries 失败 → null → 维持原空态文案，不阻塞三问主数据。
- `src/styles.css`：新增 `.ov-nav*` 系列（角标胶囊/切换 tabs/涨跌色）。
- 区分口径：卡片标注「日频运行态曲线（镜像 HP paper 产物，每交易日盘后更新）；回测口径曲线见版本页」——版本页 156 点月频回测曲线不受影响、不混入。
- 修复过程留痕：首版 `load()` 内 `p` 变量 try 块作用域引用错误导致序列不渲染，改用 `pidRef` 传递后修复（无头浏览器验证通过）。

## 4. 构建与线上验证（全部通过）

| 验收项 | 结果 |
|---|---|
| 构建 `VITE_API_BASE=/quantv6 npm run build` | ✅ 新 hash `index-u5RmvFPM.js` / `index-DL_pGBEc.css`，线上 index.html 已引用新 hash |
| `npm test`（quant-bff） | ✅ 38/38（含新增 3 例） |
| `curl https://www.zhengqiangnan.cn/quantv6/api/v1/portfolios/vC-0/navseries` | ✅ HTTP 200，11 点，首点 2026-08-14/nav 0.9996，末值 1.00993，nav_chg_1d 0.0115（+1.15%），MDD -2.55%，drawdown 0（新高） |
| 无头浏览器 390×844 总览页 | ✅ bodyScrollW=390 / docScrollW=390 无横滚；区块① navCard 渲染非空（曲线 path + 四角标 + tabs），tab 90 点击后曲线正常重渲 |
| 在役零改动 | ✅ HP 零改动（仅只读 ssh 核实文件名）；BFF 现有路由行为未变（38 测试回归全过）；crontab 未动 |
| 截图存证 | `shared/results/work/task-0560-nav-section.png`（区块①卡片）、`task-0560-overview-390.png`（整页） |

## 5. 交付物清单

- 同步通道：无 diff（既有 `--include=baseline-paper-*` 已覆盖，证据见 §1）
- BFF：`tools/quant-bff/src/nav-series.js`（新）、`src/config.js`、`src/app.js`、`test/nav-series.test.js`（新）、`fixtures/good/data/portfolios.json`（新）、`fixtures/good/data/runtime-paper-nav.csv`（新）
- 前端：`tools/quant-dashboard/src/api.js`、`src/pages/Overview.jsx`、`src/styles.css`、`dist/`（新构建）
- 笔记：`shared/results/work/task-0560-notes.md`
