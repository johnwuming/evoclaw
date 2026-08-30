# task-0580 过程笔记（B2: sleeve 字段升版 + BFF 保留腿后缀 + 前端腿徽标）

## 1. 账本 target 实查（2026-08-30）
- 账本路径：tools/quant-bff/live/events/iteration-ledger-2026-08.jsonl（20847 B，只读未改）
- 全部 target 分布：`paper/vC-0#equity`×8、`paper/vC-0`×4、`vC-0`×2、`drift/equity_sleeve`×1、`portfolio/vC-0`×1
- trade.fill 事件 8 条，target 全部为 `paper/vC-0#equity`（payload: date/code/action/shares/price/fee/source_file）
- **结论：腿后缀格式 = `paper/<id>#<suffix>`，当前账本唯一实存 suffix 为 `equity` → 映射 `equity_sleeve`；黄金腿契约枚举 `hedge_sleeve_gold`（suffix 预留 `hedge_sleeve_gold`/`gold` 映射之）；无 `#` 后缀或未知 suffix → `unknown`（如实不猜）**

## 2. BFF 现状
- projectFills 在 src/app.js:261，用前缀 `paper/${id}#` 过滤但丢弃 `#` 后缀 → P0 根因确认

## 3. BFF 改动（src/app.js，零写路径）
- 新增 `sleeveFromTarget()`：target 含 `#` 取后缀；`equity`/`equity_sleeve`→`equity_sleeve`；`hedge_sleeve_gold`/`gold`→`hedge_sleeve_gold`；否则 `unknown`
- projectFills 投影项新增 `sleeve` 字段
- 持仓聚合键 code → `sleeve|code`（双腿同代码不合并），items 每行带 sleeve，排序 code+sleeve
- trades items 每行带 sleeve
- `node --check` OK；服务名确认 quant-bff.service（read-only BFF，允许重启）

## 4. BFF 重启后 curl 实查（127.0.0.1:8180）
- /portfolios/vC-0/holdings：items 8 行全带 `"sleeve":"equity_sleeve"`；验收单行命令输出 `{'equity_sleeve'}` ✓
- /portfolios/vC-0/trades?limit=3：items 带 sleeve ✓，total.count=8 不变，字段序 ordinal/date/ts/code/action/sleeve/… ✓

## 5. 契约文档增量（R-342，55.4KB 只 grep/定位改）
- 行3 当前版本 v2.0→v2.1；契约总表标题→v2.1 收编
- #8：items 加 sleeve；降级语义加枚举+unknown 口径；数据源 target 格式改 `paper/<id>#<suffix>`、按 sleeve+code 聚合；首次实装加「sleeve v2.1（task-0580）」
- #9：items 加 sleeve（action 后）；降级语义加枚举引用；首次实装同上
- 修订记录追加 v2.1 行（task-0580，格式沿用既有条目）

## 6. 前端改动（Version.jsx + styles.css，零新依赖）
- 新增 LEG_CHIP 映射 + LegChip 组件：equity_sleeve→股票腿、hedge_sleeve_gold→黄金腿、缺失/unknown→未知（如实）
- 持仓表/交易表各加「腿」列（7 列），key 改 sleeve:code 防双腿同代码冲突
- 卡头改「持仓明细（账本投影 · 逐行腿标注）」/「交易清单（账本投影 · 逐行腿标注）」，移除表头上方仅代表股票腿的权重位（避免双腿表误标股票腿权重）
- 交易日期 390 下截为 MM-DD（t.date.slice(5)，年份全 2026；fmtID 同款截断纪律）——修 7 列后日期格 nowrap 溢出 13px 问题
- styles.css 新增 .leg-chip/.leg-equity/.leg-gold/.leg-unknown（10px 小徽标）
- 新增 scripts/t0580-headless-check.cjs（390x844 无头验收，基于 t0575 同款）

## 7. 构建与验证（最终轮）
- VITE_API_BASE=/quantv6 npm run build：✓ 零报错（index-Cnpxo1U-.js 206.15 kB）
- grep -rl quantv6 dist/assets/：✓ 命中 index-Cnpxo1U-.js
- npm test：✓ engine-copy assertions: 39 passed
- 390 无头（t0580）：T0580_CHECK_PASS——bodyScrollW=390、docScrollW=390、持仓 8/8 行+交易 8/8 行全带徽标（16 chips 全「股票腿」）、unknown=0、TD 内部溢出 0
- 修改文件清单：quant-bff/src/app.js、quant-dashboard/src/pages/Version.jsx、src/styles.css、scripts/t0580-headless-check.cjs（新）、R-342 契约文档、本笔记；账本零改动
- 验收命令复跑：curl holdings sleeve 集合输出 {'equity_sleeve'} ✓
