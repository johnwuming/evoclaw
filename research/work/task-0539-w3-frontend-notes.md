# task-0539 W3 前端骨架+事件页+迁移页 过程笔记

## 已确认事实
- BFF `http://127.0.0.1:8180`：
  - `/api/v1/events`：`{items:[{ts,event_type,target,actor,payload}], next_cursor}`；支持 `?type=`（已验证 promotion.requested→4 条）与 `?cursor=`（格式 `<ordinal>:<ts>`，坏 cursor 返回 BAD_CURSOR）；`page/page_size` 参数被忽略。响应头 `X-Ledger-Tail-Ts: 2026-08-27T01:00:00.000Z`。夹具 49 条，next_cursor=null。
  - `/api/v1/migration`：`{phase:"B", items:[{id,title,state,evidence_ref}], blocking:{a1_pass,a2_pass}}`；state∈{done,doing,todo}；现有 A1/A2(done)+B1(doing)+B2/B3(todo)；evidence_ref 形如 `shared/results/04-投资研究/r328-phase-a-audit.md`。
- 17 种事件类型：promotion.*（蓝）、risk.*（红）、weight.*（绿）、solver.*、retirement.*、reconciliation.failed（高亮）、backtest/gate/checkpoint/component/version/checkpoint（中性）。
- 待决超期口径（前端呈现）：promotion.requested 同 target 无后续 promotion.approved/rejected/executed/downgraded → 「待决」；跨度 >35 天（1 调仓周期）→ 「待决超期」。夹具中 PV-2026-08-D 为待决（08-12 申请，无后续处置，16 天）。
- PRD/R-342 关键规范：底部 5 Tab（≤768 底部 / >768 顶部）；≤390 单列无横滚（overflow-x hidden、flex/grid 百分比、触控≥44px）；表格≤560px 降级卡片；详情 drawer 不弹模态；Tab 隐藏暂停轮询、恢复立即拉取；本批轮询简化=手动刷新+60s；截图命名 `dashv6-{block}-390x844.png`。
- 零写入口：全部 GET；无表单/提交/确认控件。

## 实现决策
- Vite+React 手写最小骨架（package.json+@vitejs/plugin-react），dev proxy `/api`→8180。
- hash 路由（#/events 等）便于无头浏览器直达；路由状态与 Tab 同步。
- 迁移页：A-D 四段分组（C/D 无数据显示未开始占位）；A1/A2 置顶+blocking FAIL 红色「绝对阻塞」横幅；Phase C 动作带「需用户批准」标注（红线规则，前端预留）；证据以路径芯片呈现（BFF 无文件服务端点，不做跳转，避免假链接）。
- 事件页：倒序+类型下拉过滤（走 API ?type=）+「加载更多」（next_cursor）+徽标+待决/待决超期打标；顶部轻量新鲜度条（X-Ledger-Tail-Ts+最后刷新时间）。
- 事件类型下拉选项=硬编码 17 种（与账本口径一致），另含「全部」。

## 验证记录
（追加中）
