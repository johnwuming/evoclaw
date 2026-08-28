# task-0532 Dashboard 产品方案 PRD — 过程笔记

开始时间：2026-08-28 19:1x。边查边写，本文件为唯一证据落点。

## 输入文件确认
- R-342：30389B（略超30KB → 分段读，先抓标题结构）
- R-336：52927B（>30KB → 分段读）
- R-344 文件名未被占用（ls 确认，最大编号 R-342）
- agent-dashboard：server.js 718KB（禁全读，只 grep 路由/模块名）；PROGRESS.md 2.5KB、CLAUDE.md 1.7KB、V4-DESIGN.md 12.5KB（可读）

## R-342 第4章 Dashboard 设计要点（已读 L179-298）
- 心智转换：旧量化Tab=「产物文件浏览器」→ 新=「组合治理驾驶舱」，打开即答三问：组合什么状态/谁在管风险/迁移到哪一步
- 技术栈：推荐 Vite+React SPA + Express BFF（产品文档不展开实现，只知 BFF 只读零写面）
- 六区块：①总览驾驶舱(NAV曲线/回撤带位/在役PV/对账徽标,60s) ②引擎卡片(shadow/paper/live/archived,IC+ICIR+信号日+天数,300s) ③组合版本视图(版本树+状态机胶囊流,300s) ④事件流水(type着色+actor+payload摘要+过滤+cursor分页,120s) ⑤风控闸门(回撤4带<5/5-10/10-15/>15、vol±2pp、相关性三档0.75/0.85/0.90、漂移D1-D4、断路器,120s) ⑥迁移进度(Phase A-D done/doing/todo+证据链接,A1/A2置顶阻塞,600s+手动)
- 实时性：HTTP轮询 60/120/300/600s 分频，不用 SSE/WebSocket；全局健康条 sync_lag_seconds 超阈黄色「数据非最新」
- 390px 硬约束：≤390 无横向滚动；单列+底部Tab；表格→卡片；状态机→2行折返；触控≥44px；详情用 drawer/bottom-sheet；390×844 截图基线
- 过渡：并行新建→双看板对照≥1个调仓周期→nginx路由切换、旧看板降 /legacy 保留≥1周期→Phase D 归档
- API契约 10 个 endpoint（§3.4）：overview/engines/portfolios/portfolio详情/timeline/events/risk.gates/risk.drift/migration/health，全 JSON、cursor 分页、BFF 零写面

## R-342 第5章排期（W1-W9）
- W1 事件流水读取层 | W2 只读API(events/portfolios/health) | W3 前端骨架+区块④⑥ | W4 驾驶舱+引擎卡+版本视图(卡PhaseB动作1 vC-0快照) | W5 风控闸门+对账徽标(卡PhaseB动作4/5) | W6 双看板验收 | W7 切换准备(Phase C批准后) | W8 切换+观察 | W9 收尾归档
- 原则：事件流水API先行是地基；旧看板不下线，全程观测能力不断档

## 旧看板能力盘点（进行中）
