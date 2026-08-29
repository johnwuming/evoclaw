# task-0557 笔记：模拟盘三视图 + 模型说明卡

## 数据源决策（2026-08-29）
- VPS live/data/ 无持仓/交易投影文件；VPS live/events/iteration-ledger-2026-08.jsonl 仅 2 事件（version.created+weight.solved）。
- HP 账本 ~/quant-evolve/portfolio_v1/portfolio/events/iteration-ledger-2026-08.jsonl 共 16 事件：2 PhaseB + baseline/calibration/pointer 3 + trade.fill×8 + reconciliation×2 + checkpoint×1。
- 本地 2 事件与 HP 前 2 条 JSON 级完全一致 → 用 HP 文件原子替换 VPS live/events 同名文件安全（链权威在 HP，R-354 已确认）。
- **选方案 A（BFF 读时投影）**：把 HP 账本拉到 VPS live/events/（一次性 scp，HP 只读零改动），BFF 从 ctx.events 投影 holdings/trades，无写路径。理由：改动最小（不动同步管道、不在 HP 加导出脚本）；ensureFresh 已有账本重读机制，未来账本更新后 BFF 自动可见。持续同步缺口 → 登记后续任务（不动 crontab，按量化纪律 crontab 变更需用户批准）。
- 事件 payload 结构（trade.fill）：{date:"2026-08-14", code:"300824", action:"buy", shares:"900", price:"7.74", fee:"7.74", source_file:"results/baseline-paper-trades.csv"}，target="paper/vC-0#equity"，数值均为字符串需 parse。
- 无 nav.daily 事件；每 code 无独立现价源 → last_price 用该 code 最近成交价（price_basis: last_fill），市值=shares×last_price，权重=市值占比。

## BFF 实现要点
- app.js：ledgerDerived 包裹（账本 503 断路器语义一致）、ID_RE 校验、分页 cursor=`${ordinal}:${ts}` 对齐 events 路由。
- GET /portfolios/:id/holdings：items[code,shares,cost_price,last_price,market_value,weight]，头 total_market_value/as_of/price_basis/source。
- GET /portfolios/:id/trades：items[ordinal,date,ts,code,action,shares,price,fee] 倒序+cursor/limit 分页；**fee 汇总并入响应头**（total_fee/buy_count/sell_count/buy_fee/sell_fee）——选并入理由：三视图一页同屏，省一次请求；fees 独立路由无独立消费场景。
- 现有基线：npm test 30/30（待跑确认）。

## 前端
- Version.jsx 接入：持仓表+交易表+手续费汇总卡+模型组成说明卡（sleeve×2+风控+求解器，从 vC-0.json sleeves/risk_control/solver 渲染）。
- ⚠️ build 必须 VITE_API_BASE=/quantv6。

## 进度（2026-08-29 14:0x）
- ✅ HP 账本已拉取并原子替换 VPS live/events/iteration-ledger-2026-08.jsonl（16 事件，原 2 事件备份 /tmp/vps-ledger-backup-2ev.jsonl）。
- ✅ BFF 新增 portfolioHoldingsHandler/portfolioTradesHandler（app.js），路由 /portfolios/:id/holdings 与 /trades，套 ledgerDerived+ID_RE，fee 汇总并入 trades 响应头 total。
- ✅ npm test 33/33（基线 30 + 新增 w7-holdings-trades.test.js 3：持仓投影含卖扣减/权重和=1/版本隔离、trades 分页不重不漏+fee 汇总、空态/坏 id）。
- 测试坑：新测试文件模块级 server 必须 after(close)，否则 keep-alive 挂住进程不退出。
- 下一步：前端 Version.jsx 接入 → build（VITE_API_BASE=/quantv6）→ 部署 → HTTPS 端到端 → 无头浏览器 390x844。
