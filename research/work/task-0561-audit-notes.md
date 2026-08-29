# task-0561 新看板未生效模块对照审计 — 笔记

开始时间：2026-08-29 14:30 ｜ 纯只读审计

## 0. 环境事实
- 前端页面：tools/quant-dashboard/src/pages/{Overview,Risk,Version,Events,Migration,Placeholder}.jsx（44KB 总量，全量可读）
- BFF：tools/quant-bff/src/app.js（19KB）
- 数据投影：tools/quant-bff/live/data/（engines.json 775B, migration.json 708B, nav_curves.csv 23KB, overview.json 130B, perf_history_index.json 9.7KB, performance.*.json 6 个版本, portfolios.json 422B, versions/ 目录, governance/ 目录）
- 报告编号：R-357 为当前最大（无 R-358/R-359）→ 本任务落 R-358？任务书指定 R-359。ls 确认最大为 R-357，为避免撞号采用任务书指定 R-359（间隔留白可接受，并在报告头注明）
  - 修正：任务书明确说"确认 R-358 为最大"，实际最大是 R-357。检查 .task-completions.jsonl 无 R-358 记录。稳妥起见先再查一次全 results 树，若无 R-358 则用 R-358（顺延），避免跳号；有则用 R-359。
- PRD = R-344（26.6KB，已读 §1-§6）；R-342 = 45KB（>30KB 只抽 §4.3/§1.2）

## 1. PRD 承诺清单（R-344 提取）

### 全局元素（§2.2）
- G1 健康条：数据新鲜度（同步滞后秒数）+ 投影校验状态；超阈值变黄「数据非最新」横幅；净值停摆≥2交易日→红色「自动决策已冻结」
- G2 风险角标：待处理风险→风控 Tab+健康条红点；计数=待处理事项聚合条目数

### Tab1 总览
- 区块① 驾驶舱 P0：净值曲线(30日窗,P1加90日/1年切换)、日变动%、当前回撤+四带带位、在役版本卡(版本号+状态+sleeve权重堆叠条)、三方对账徽标(P0红绿+触发时间,P1差异明细抽屉)、数据新鲜度
- 区块② 引擎卡片 P0：每sleeve一卡：状态(shadow/paper/live/archived)、最新IC+3月趋势(老化标黄)、ICIR_OOS、最近信号日、paper/shadow已进行天数；P1交互：信号明细抽屉、点状态跳版本页

### Tab2 风控
- 区块⑤ 风控闸门 P0：六组闸门=当前值+带宽+状态：回撤四带(仪表)、波动率带(8%±2pp)、两腿20日相关性(0.75/0.85/0.90三档)、漂移四维D1-D4(20bp/0.3/90%+95%/×1.5+连续超带期数)、断路器状态(触发→顶部红条+原因+时间)、退役监视(P1:RET-1..4余量)
- P1 待处理事项视图：聚合断路器/对账失败/漂移超带/退役review

### Tab3 版本
- 区块③ P0：在役版本卡高亮、状态机胶囊流(approved→paper→live,当前段高亮,canary不入主图)、版本列表(状态过滤)
- P1 版本详情抽屉：sleeve清单(component_ref+code_hash+data_cut)、风险控制配置、门禁成绩单(gate_report逐条pass/fail+阈值+实测值)、权重方案、求解留痕(solver_id+参数+fallback原因)、版本树(parent_version链)
- P2 两版本diff

### Tab4 事件
- 区块④ P0：倒序时间线、17种事件类型着色(晋升蓝/风控红/求解绿/对账失败高亮)、每条=时间+类型+对象+执行者(pipeline/user/risk_layer)+摘要；P0交互=类型/执行者/对象过滤+分页50条
- P1：点降级事件展开触发规则+实测值vs阈值、对账失败差异明细、晋升批准显示批准人时间

### Tab5 迁移
- 区块⑥ P0：四阶段卡片(A审计/B影子/C治理/D退役)、动作done/doing/todo+证据链接、A1/A2置顶(FAIL=红色绝对阻塞)、Phase C需用户批准红线标注
- P1：双看板并行对照验收项

### 非功能（§6）
- N1 数据新鲜度分频轮询 60/120/300/600s
- N2 事件≤5min可见；投影校验不一致显示对账失败状态条不静默用旧数据
- N3 零写入口
- N4 390px 无横向滚动
- N5 首屏≤2s

## 2. 已知项（排除重复报告，但表内保留标状态）
- K1 总览区块① NAV与回撤 → task-0560 进行中
- K2 引擎卡 IC待接入/最近信号待接入 → 已知待接投影
- K3 版本页持仓/交易/fee三视图 → task-0557 已生效
- K4 版本页四指标+NAV曲线 → task-0553/0555 已生效
- K5 说明卡版本化 → task-0558 已生效

## 3. 代码核验（进行中…）
