# task-0323 开发笔记（QTV4-P3 生命周期层）

## 任务
server.js 新增 `/api/quant/lifecycle` API + ⑥生命周期层 UI（决策时间线/实验台账/迭代轨迹散点/A2管线视图），挂在 btlc 页 P2 验证层之后、e2e 趋势图之前。

## 结论（全部验收通过，22:22 收口）

### 验收命令结果
1. `node --check server.js` → SYNTAX_OK；`systemctl is-active agent-dashboard` → active
2. `curl -s 'http://127.0.0.1:8055/api/quant/lifecycle' | head -c 500` → `{"ok":true,...,"decision_id":"D-20260816-SEEDB-RESET"...}`；完整 JSON（/tmp/task0323-lifecycle.json）确认 ledger 含 IT-001（baseline_v0_seed）
   - ⚠️ 任务书预期「D-20260816-Q4B-BC」，但 decision-log.jsonl 实际当前唯一记录是 D-20260816-SEEDB-RESET（任务书笔误）。API 动态读文件，A2 追加 D-20260816-A2-* 后自动出现
3. `curl -s http://127.0.0.1:8055/ | grep -c 'lifecycle\|迭代轨迹'` → 11（>0）
4. CDP 截图（playwright-core@1.61.1 + google-chrome，脚本 /tmp/task0323-shot.js）：
   - /tmp/task0323-quant.png（904x814 生命周期区块整段）：四组件 DOM 断言 pipeline/timeline/ledger/scatter_canvas 全 true，页面含 D-20260816 与 IT-001
   - /tmp/task0323-mobile.png（390x844 视口，区块元素截图）：bodyScrollW=390（无横向溢出）

### 交互验证（/tmp/task0323-interact.js，DOM 断言）
- 散点图：Chart 实例存在，数据集「未裁决（1）」1 点（IT-001 基线无裁决 → 灰点，符合规格）
- ledger_reset 行灰色分隔条：存在
- 决策条目点击展开原始 JSON：true
- 口径切换 locked：locked 列变 700 粗体 + 散点 y 切为 26.26（=0.2626×100）✓
- P1/P2 未动且完好：基线卡「基线回测」/「五门禁面板」/「版本切换器」均渲染
- pageerror：无

## 实现清单（server.js，备份 server.js.bak-task0323-20260816-220941）
1. **服务端** `/api/quant/lifecycle`（约 L2568-L2640，挂在 /api/quant/ledger 之后）：
   - decisions：读 results/model/decision-log.jsonl（缺失回退 model/，decision_source 字段标注），倒序，summary 取 decision||note||trigger||action，raw 透传
   - ledger：读 results/experiment-ledger.jsonl，行序编号（ledger_reset 不编号，baseline_v0_seed=IT-001 顺延），verdict 归一 pass/reject/pending/null，full/locked/params/pool 透传，倒序
   - registry：现周期=results/model/ 动态扫描 *.json（v0_seed + A2 未来注册的 v1.x 自动出现，status 缺省 v0_seed→active）；active 判定 status=active > v0_seed > created_at 最新；旧周期 model/registry/ v1.1-v1.4 标 archived 只计数（避免误报「新版本已 activate」）
   - 空态：qlcReadJsonl 缺文件/空文件返回 []（node 单测验证过 missing/empty/bad-line 三态不炸），ok:true + note，不 500
2. **前端**（挂在 drawDsrCurve 之后、loadPaperQuant 之前）：
   - renderBtlcPage：quantBaselineCard 后插 `<div id="quantLifecycleRoot">`（两分支共用）；两处 loader 调用点各加 loadQuantLifecycleLayer()
   - renderLifecycleLayer：区块标题+quantConceptBadge('D- 决策 / IT- 迭代')+「版本 vs 迭代」常驻说明（R-214 §1.5）
   - qLifecyclePipeline：active≠v0_seed → 「✨ 新版本已 activate：V-v1.x」绿高亮；有新 IT 行 → 最新 IT 卡片（策略/参数/年化/回撤/Sharpe/调仓/pool chips/裁决徽标）；基线仍是最新行 → 「⏳ A2 迭代进行中（HP），暂无新试验落盘」中性态；现周期版本 chips（active ★绿）+ 旧周期归档计数
   - qLifecycleTimeline：垂直时间线（左侧 2px 竖线+accent 圆点），fmtID(D-) + ts + 摘要，点击展开原始 JSON（_qLifecycle.expandD），空态「暂无决策记录」
   - qLifecycleLedgerTable：IT-/ts/event/策略/pool chips/full 年化/locked 年化/裁决徽标；full↔locked 切换按钮（复用基线卡口径切换模式）；ledger_reset 灰色 colspan 分隔条
   - qLifecycleScatterSection + drawLifecycleScatter：Chart.js scatter，x=线性刻度+IT 标签 ticks，y=年化%（随口径切换），按裁决分数据集着色（PASS 绿/REJECT 红/进行中黄/未裁决灰），tooltip 显示完整指标（年化/回撤/Sharpe/调仓/年限/pool）；点少正常渲染，无点/无该口径数据时 placeholder
3. **动态刷新**：loadBtlcQuant 的数据签名纳入 lifecycle API（A2 追加行 → 签名变化 → 自动重渲染；用户切 tab force=true 必重拉）

## 关键事实备忘
- 新周期 registry = /root/.openclaw/workspace-quant/results/model/（v0_seed.json，字段 version/strategy/params/factors/context/baseline/registered_at）；旧周期 = model/registry/ v1.1-v1.4（readRegistryVersions 读的是旧路径，v1.4 status=active 是归档遗留，不能当现役）
- ledger 行结构：{ts,event,task,strategy,pool,full:{years,ann,mdd,sharpe,n_rebalance},locked:{...},log}
- Chart.js 本地化 /chart.umd.min.js，前端全内嵌 getDashboardHTML()
- 主导航 #page=quant hash 路由；子 tab switchQuantTab('btlc', true)
