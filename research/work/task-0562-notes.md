# task-0562 看板小修包 P1 笔记

## 0. 任务范围
- 前端4项: a)TabBar风险角标(pending_risks.count) b)HealthStrip投影校验位 c)Version详情risk_control块 d)Events actor/target过滤
- migration.json: B2/B3→done(据R-349), 补Phase B动作1-5(R-346/347/348), 补Phase C行(R-354已完成)与Phase D行(规划中), 备份.bak
- R-342增补「契约与现实对齐(2026-08-29)」节: /risk/drift与/portfolios/:id/timeline列为后续版本项(引R-359 B1/B2)
- 构建 VITE_API_BASE=/quantv6 + npm test + 无头390x844验证
- 不改BFF代码

## 1. R-359 审计要点摘录
- G3: TabBar.jsx(20行)无角标; health.pending_risks.count 可用
- G2: /health 已返回 projection_sha256_ok=true; HealthStrip 未显示
- V5: BFF detail 返回 risk_control.drawdown_gates(宪章25%/35%); Version.jsx 未渲染
- E3: Events.jsx 类型过滤✓; actor/target 无UI, 数据在 items 内
- M5/M1: migration.json 静态5行; B2(MVO对照)/B3(协方差对比)已由R-349完成; Phase B动作1-5=R-346(动作12 vC0快照+等波动率求解器)/R-347(动作3 选择器化+vC0复现门)/R-348(动作45 影子对账+漂移监控基建); Phase C=R-354 治理切换已完成(2026-08-29)

## 2. 已完成改动（证据）
- TabBar.jsx 重写: 新增 riskCount prop, count>0 时「风控」Tab .tab-risk-dot 红点(title/aria 带 count)
- App.jsx: +useState riskCount +usePoll 60s fetchHealth → 传 riskCount 给 TabBar
- HealthStrip.jsx 重写: 内部 usePoll 120s fetchHealth → projection_sha256_ok true→「投影✓」false→「投影✗」null→不渲染(空态降级)
- Version.jsx: 新增 RiskControlSection 组件(回撤闸门在役宪章 减半/清仓/宪章版本/口径来源/note/vol_target 未设定/backfill_rule), Detail 中 PaperViews 后渲染(仅 detail.risk_control 存在时)
- Events.jsx: +actorF/targetF 两状态, actors/targets 由已载入 items 去重导出, visible 三条件与过滤, 第二行 filter-row 两个下拉(option 文本 fmtID(t,24) 防长ID)
- styles.css 末尾追加: .tab-label position, .tab-risk-dot(8px 红点 var(--red)), .health-proj ok/bad
- esbuild 转译 5 文件全过(语法验证)
- migration.json: 备份 migration.json.bak-20260829; 5→12 行; B2/B3→done(证据 R-349 路径); 新增 B4-B8=动作1-5(R-346/347/348); C1 done(R-354); D1 todo; blocking 原样保留; B1 保持 doing(审计未标记,范围外); **phase "B"→"D"(判断项: A/B/C 全完成,D 为当前段,消除「当前阶段B」失真——已在报告标注可回退)**
- meta 头: 按 projection.json 约定 canonicalJson(items) sha256 + generated_at + note; BFF migrationHandler 只透传 phase/items/blocking, meta 仅文件级留痕不影响 API
- projection_sha256_ok 不受影响: revalidateProjection 只校验 projection.json(registry/engines/composites)
- R-342(45KB 未全读): 文末追加「契约与现实对齐(2026-08-29)」节 + 修订记录 v1.3 行后无 v1.4 条目行(按文件既有追加惯例,未动 v1.x 编号体系); 只增不删
  - 注: 实际操作=在 v1.3 行后直接插入新节(修订记录条目行未新增,避免伪造版本号;新节自带依据与日期)

## 3. 验证结果（无头 390x844，本地 dist+反代 8180 BFF，截图 shared/results/work/q562-shots/）
- 五 Tab scrollWidth 全部 =390，无横向滚动（含版本详情展开态）
- 投影✓ chip：五 Tab HealthStrip 全部出现（projection_sha256_ok=true）
- TabBar 角标：自然态 pending=0 无红点（正确降级）；mock health pending_risks.count=2 → 「风控」Tab 红点可见，title「待处理风险 2 项」，截图 overview_badge.png
- 版本详情 risk_control：区块渲染 ✓，「减半 25% · 清仓 35%（宪章 v1.0）」✓，口径 note ✓，vol_target「未设定」✓
- 事件页过滤器：3 个下拉（类型16/执行者3/对象5）；选执行者后 16→2 条且 actor=risk_layer ✓
- 迁移页：动作1-5 全渲染 ✓，C1 治理切换=完成 ✓，D1=未开始 ✓，Phase D 段挂「进行中」标 ✓，C1 done 后无「需用户批准」标 ✓，done chips=12（10 项 + A1/A2 置顶重复计数），B2/B3 证据含 R-349 ✓
- npm test：dashboard 39 断言全过；BFF 38 pass/0 fail（migration.json 数据变更不破坏 BFF 测试）
- VITE_API_BASE=/quantv6 npm run build ✓（43 modules，dist/）
- BFF /api/v1/migration 实测返回 12 行/phase D/B2B3 done（curl 落 /tmp/q562/migration.json）
- 清理：本地验证 proxy 已杀（8899 关闭）；生产部署不在本任务范围（dist 未发布）

## 4. 报告
- R-360：shared/results/05-量化投资/R-360-看板小修包P1.md（编号确认：results 树当前最大 R-359，R-358 预留 task-0560）
