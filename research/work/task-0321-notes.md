# task-0321 过程笔记 [QTV4-P1] 量化Tab数据接通

## 1. 现状核验

### 数据文件（VPS /root/.openclaw/workspace-quant/results/）
- seedB_v0_{full,locked}_{metrics,nav,yearly,trades,holdings}.csv/json 共12个，2026-08-16 21:21 就位
- full_metrics.json: annual_return 0.2635 / max_drawdown -0.6949 / sharpe 0.9027 / calmar 0.3791 / cumulative_return 122.8777 / monthly_win_rate 0.587 / period 2006-01-04~2026-08-14 / years 20.61 / cost_model v2 / limit_board on
- nav CSV 表头 `date,nav,num_held`；full 5008 点 / locked 4491 点（均>200 ✓）
- yearly CSV 表头 `year,return`
- 旧文件 backtest_dividend_quality_* 已不存在（归档），基线API需直接切新名，不留fallback ✓（任务书要求）

### registry v0_seed.json（workspace-quant/results/model/v0_seed.json）
- version=v0_seed, strategy=dividend_quality_smallcap_seedB
- context: universe=全量池（存活qfq ∪ 退市hfq panel，299只/44005行）、cost_model=cost v2、limit_up_filter=一字板不可买、audit_lock=AUDIT_LOCK_END=2024-06-30、gates=五门禁（g1-g5）
- factors: div_yield_ttm/roe_ttm/roa_ttm/circ_mv

### server.js（580KB，禁止全读）
- L2650 QUANT_BASELINE_DIR='/root/.openclaw/workspace-quant/results'
- L2653/2658/2678 三个 baseline API 硬编码读 backtest_dividend_quality_{metrics.json,nav.csv,yearly.csv}（旧名）→ 需改为 seedB_v0_<window>_<...>，支持 ?window=full|locked（默认full）、?version=v0_seed（文件名 pattern: seedB_<version>_<window>_*）
  - 注意：任务书 pattern 是 `<strategy>_<version>_<window>_*`，当前 strategy=seedB → 文件名 seedB_v0_seed_full_metrics.json？不对——实际文件名是 seedB_v0_full_metrics.json。核对：实际文件 seedB_v0_{full,locked}_*。即 pattern 为 `seedB_<version?>_<window>_*.json`，其中 "v0" 应是 version 的显示（V-v0）。registry version=v0_seed，但文件名用的是 v0。结论：文件名前缀当前固定 seedB_v0_，version 参数预留：window/version 参数先实现 window 切换；version 查表映射到文件名前缀（默认 'seedB_v0'）。为满足 `?version=v0_seed` 预留，实现 version→文件前缀映射表 {v0_seed:'seedB_v0'}，未知version返回404/空。
- 前端：量化Tab 5个子页 data/factor/models/btlc/paper（quant-page-*）；基线API当前无前端调用方（历史遗留），本次新增基线回测卡挂在 btlc 页顶部消费
- btlc 页 renderBtlcPage（~L9440+ 待详查）→ 版本切换器/归因链/M3.1对照卡/M3.2净值图/M3.3分年度
- 数据页 loadDataQuant（L7930起，灰卡在 data tab）
- e2e趋势图 quant/e2e-curves L9683 附近
- readJsonFile 定义于 L1827（在 baseline API 之前，可用）

## 2. 改动方案

### server.js 后端
1. baseline API 三接口改读 seedB：新 helper `quantBaselineFile(kind, version, window)` 生成路径
   - summary: `<prefix>_<window>_metrics.json`
   - nav: `<prefix>_<window>_nav.csv`（保留原CSV解析，补 window/version 参数）
   - yearly: `<prefix>_<window>_yearly.csv`
   - `window` 白名单 full|locked（默认 full），version 白名单映射（默认 v0_seed），响应附加 meta: {version, window, strategy, file 前缀}
2. 新增 GET /api/quant/baseline/meta：返回 registry context + SNAP/PAN 常量（底座徽标数据源）
   - SERVER-side 常量表：SNAP='20260814'（来源：qfq 快照最后交易日 2026-08-14）、PAN='v3'（财务面板版本，data/derived）、pool=registry.context.universe
   - 实际读 v0_seed.json 的 context 映射；SNAP/PAN 值配在 server 常量，注释注明来源
3. node --check + systemctl restart agent-dashboard

### 前端（server.js 内嵌 JS）
4. 全局 fmtID(raw, concept)：按 R-214 §1.5 前缀表（SNAP-/PAN-/F-/V-/T-/IT-/D-/R-），裸 id 补前缀；已带前缀不重复加；挂 window 全局供 P2/P3 复用，带注释
5. btlc 页顶部新增「基线回测卡」：
   - fetch /api/quant/baseline/summary?window=X&version=v0_seed + /api/quant/baseline/meta
   - 指标：年化/回撤/夏普/Calmar/累计/月胜率/区间
   - 口径徽标「全量池+成本v2+一字板+审计锁」；full/locked 切换按钮（切换重取数）
   - 底座徽标 SNAP-20260814 · PAN-v3 · 全量池（角标）
   - 标题概念徽标〔ID：V-〕，版本显示 fmtID('v0_seed','V')
6. 区块概念徽标：数据页灰卡区块〔ID：SNAP-/PAN-〕、btlc e2e趋势图〔ID：V-〕、基线卡〔ID：V-〕
7. CDP 390x844 截图验证

### rsync
8. auto_sync_notify.py 同步范围覆盖 seedB_* 与 q4b*（备份后改，dry-run 验证）

## 3. 执行记录
- [21:30] 备份 server.js → server.js.bak-task0321-<ts>
- [21:27] server.js 已备份 server.js.bak-task0321-20260816-212747（580899B）
- [21:30] 前端结构确认：量化Tab 5子页(data/factor/models/btlc/paper)；基线API当前无调用方 → 新增基线回测卡挂 btlc 页 renderBtlcPage（9767行）版本切换器之后、!data.available 早退之前（seedB 卡独立于旧 btlc 管线，始终渲染）
- api() 助手 L6049、esc() L6058、fmtPct L10267；CSS 变量 --card/--sub/--fg/--green/--red/--amber/--accent/--border/--fill 均在用
- e2e 趋势图标题在 renderBtlcE2E（L9587，chart-title）；数据灰卡在 renderDataQuant M1.1 区块（L7963 quant-section-title）
- auto_sync_notify.py（496行）：VPS 上跑、ssh 拉 HP(10.12.192.174)~/quant-evolve/results/ → VPS shared/results/04-投资研究/；model/ → workspace-quant/model/。缺：results→workspace-quant/results/ 镜像（看板读取路径）→ 加 Step4.5 mirror：include seedB_*/q4b* + 复用 RSYNC_EXCLUDES + exclude *
