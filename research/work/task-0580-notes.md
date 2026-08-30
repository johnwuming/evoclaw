# task-0580 过程笔记（B2: sleeve 字段升版 + BFF 保留腿后缀 + 前端腿徽标）

## 1. 账本 target 实查（2026-08-30）
- 账本路径：tools/quant-bff/live/events/iteration-ledger-2026-08.jsonl（20847 B，只读未改）
- 全部 target 分布：`paper/vC-0#equity`×8、`paper/vC-0`×4、`vC-0`×2、`drift/equity_sleeve`×1、`portfolio/vC-0`×1
- trade.fill 事件 8 条，target 全部为 `paper/vC-0#equity`（payload: date/code/action/shares/price/fee/source_file）
- **结论：腿后缀格式 = `paper/<id>#<suffix>`，当前账本唯一实存 suffix 为 `equity` → 映射 `equity_sleeve`；黄金腿契约枚举 `hedge_sleeve_gold`（suffix 预留 `hedge_sleeve_gold`/`gold` 映射之）；无 `#` 后缀或未知 suffix → `unknown`（如实不猜）**

## 2. BFF 现状
- projectFills 在 src/app.js:261，用前缀 `paper/${id}#` 过滤但丢弃 `#` 后缀 → P0 根因确认
