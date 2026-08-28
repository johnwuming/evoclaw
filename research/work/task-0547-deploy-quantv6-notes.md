# task-0547 部署笔记（quantv6）

## 0. 基线探查
- quant-bff.service 存在（1433B），LEDGER_DIR 当前=fixtures/good，需改 live/events
- live/events/ 含 iteration-ledger-2026-08.jsonl
- vite.config.js 无 base；src/api.js 4469B，fetchEvents 用 new URL('/api/v1/events', origin)
