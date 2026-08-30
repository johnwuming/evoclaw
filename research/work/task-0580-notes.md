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
