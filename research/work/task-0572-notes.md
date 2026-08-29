# task-0572 过程笔记：Dashboard 迭代候选库视图

## 数据契约（R-342 v2.0 契约总表 #12/#13，唯一权威）

**#12 GET /perf-history → `perf_history@v1`**（独立文件源，不随账本 503；索引缺失→空列表降级）
- `schema / generated_at(nullable) / caliber_ref`
- `versions[]`: `{portfolio_version_id, label, kind('active'|'iteration'), status('active'|'historical'), available:true, metrics{ann_return,ann_vol,sharpe,max_drawdown}|null, data_start, data_end, n_months, has_curve:bool, cross_check_match}`
- `skipped[]`: `{portfolio_version_id, label, kind:'skipped', status:'skipped', available:false, reason(nullable), source(nullable)}`

**#13 GET /perf-history/:id → `perf_history_detail@v1`**
- `{schema, performance: null | {...perf, nav_curve:[{date,nav}]|null}}`
- perf 另含 `caliber{frequency,ann_return,ann_vol,sharpe,max_drawdown,...} / curve_source / cross_check_ref / data_as_of`
- 降级：缺失/ID 不匹配/曲线列不存在 → `performance:null`（不 503）；前端如实显示「指标缺失」，不伪造。

## 实测数据（BFF live/data，2026-08-30）
- versions 7 条：vC-0（active，实时读 performance.json）+ F0_buyhold50/F1_equal/F3_volparity/F4_erc/F5_b50_tilt65_80/F7a（historical）
- skipped 3 条：F6（无曲线产物）、F7b（无曲线产物）、paper-r309（仅 7 交易日日频，无月频回测曲线）
- metrics 四指标：ann_return/ann_vol/sharpe/max_drawdown；曲线来源 curve_source{file,column}
- active 条目 metrics 同构（四指标），data_as_of 字段存在

## 落位决策
**独立 hash 路由 `#/candidates`，不进 TabBar；入口挂在「版本」页头部 + 候选库页内返回按钮。**
理由：
1. R-342 §4.5 Tab≤5，现有 5 Tab（总览/风控/版本/事件/迁移）全部已实装，无位可替换——Placeholder 组件已不被 App.jsx switch 引用（W4-W6 后成为死导入），「替换占位」选项不成立；
2. 候选库是全量迭代组合级对照（含负结果/跳过），与版本页（现役版本运行态+状态机）信息焦点不同，混排会稀释版本页；
3. 独立 hash 路由零依赖新包、不改 TabBar 结构，Tab 约束不破坏。
- hooks.js TAB_IDS 增 `candidates`（路由白名单），TabBar 不加 Tab；直接访问 `#/candidates` 可达。

## 字段映射（视图 → 契约）
- 页头汇总：generated_at（fmtTime）、caliber_ref、versions.length、skipped.length
- 版本卡：portfolio_version_id（fmtID 截断）+ label + kind 徽章（现役/迭代）+ 四指标卡（ann_return 红绿、max_drawdown 恒 down 色、sharpe≥1 up）+ data_start~data_end + n_months + has_curve + cross_check_match（✓/未核）
- 负结果：ann_return<0 的条目照常渲染在列表中（不隐藏不折叠），收益值标 down 色；sharpe<0 同理如实标色
- 展开详情：fetchPerfHistoryDetail(id) → performance null → 显「指标缺失（performance:null）」；nav_curve null/短 → 不画图只显说明；有曲线 → 本地 SVG 轻量折线（无依赖，viewBox 自适应 390px）
- skipped 区块：默认全展开，逐条 portfolio_version_id + label + reason + source；空 → 「无跳过迭代」空态

## 约束遵守
- 本批零 BFF 改动（app.js/perf-history.js 未动）、零新依赖、不改 nginx、不重启服务
- fmtID 截断长 ID；无横向滚动目标 bodyScrollW=390
- 契约缺口记录：暂无（#12/#13 字段足够；active 条目 cross_check_match=null → 显示「未核」而非伪造）

（后续验证输出摘录见文末）

## 验收验证输出摘录（主 agent 独立复跑补录 2026-08-30 07:04）
- `VITE_API_BASE=/quantv6 npm run build` → ✓ 44 modules transformed, built in 2.00s，零报错
- `grep -rl quantv6 dist/assets/` → dist/assets/index-BU9OzPbo.js（base 注入产物确认）
- `npm test` → engine-copy assertions: 39 passed
- 负结果判定修复确认：negative 现读 `v.metrics.ann_return`（子代理自曝 bug 已修复，主 agent 实读源码+复跑构建核验）
- 390 静态自查（无头浏览器本批不可用，按纪律降级）：新组件无固定宽表格、长 ID fmtID 截断 4 处、nowrap 均为既有 overflow+ellipsis 模式，无横向滚动风险源
- 改动文件清单（全量）：src/pages/Candidates.jsx（新增）、src/App.jsx（路由+入口分发）、src/hooks.js（TAB_IDS 白名单）、src/styles.css（cand-* 样式 23 处）、src/pages/Version.jsx（候选库入口按钮）；api.js 未动（封装已有）；BFF/nginx 零改动
