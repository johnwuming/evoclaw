# task-0583 过程笔记（B7 原则编译化：lint + policy）

## 现状核验（边查边写）

- [文件大小] engines.json=775B, performance.json=1619B, perf_history_index.json=9.7KB, perf-history.js=6KB, Candidates.jsx=20KB → 均可按需读取。
- [检查① 引擎层] live/data/engines.json 实文件：两条引擎条目字段 = sleeve_id/engine_id/status/ic_latest/icir_oos/last_signal_date/paper_or_shadow_days/pv_ref/data_cut/description → **无 ann_return/ann_vol/sharpe/max_drawdown/nav_curve/metrics，现状合规**。
- [检查① BFF 处理器] src/app.js:186 enginesHandler 直接透传 data/engines.json 的 engines 数组（`{engines: doc.engines||[]}`），无注入绩效字段；BFF 无 src/engines.js，engines 通道 = app.js enginesHandler + engines.json → 断言点：engines.json 条目 + handler 源码不新增硬编码绩效。
- [检查② 口径] performance.json curve_source.column=**F1_quarterly**；metrics 含 ann/sharpe 等（现役通道，允许）；无 cross_check_match 布尔。policy current=f1_quarterly_50_50_static_quarterly ↔ column F1_quarterly 映射；authoritative_available=false → 必须有近似口径警示：Candidates.jsx:119 `<div className="cand-warn-line">⚠ 数据口径核验中（B0）…` 与 :291 cand-badge-warn 徽标 → **在场，合规**。
- [检查③ ablation 区] Candidates.jsx ablation 块边界：`{/* 构建层 ablation 对照` 注释起，至 `</details>` 止（`跳过迭代` 前）。表头 = 版本/构建方法/核验/状态（无绩效词）；块内唯一含「年化/波动/夏普/回撤」的行是 cand-abl-note 免责声明「**不含**年化/波动/夏普/回撤等绩效指标」→ lint 需放行含「不含…绩效」的免责行，其余命中即违规。主区指标卡（:155-158 年化/波动/夏普/回撤）在 ablation 块外，不受约束。
- [检查④ perf-history.js] 现状：`metrics: perf.metrics ?? null` 为数据透传（per 版本文件驱动，非硬编码）；已知硬编码 `cross_check_match: null`（:84 activeEntry）非绩效指标。lint 禁用模式 = `ann_return|ann_vol|sharpe|max_drawdown|nav_curve` 后跟数字字面量或硬编码对象（如 `metrics: {`），透传 `perf.metrics ?? null` 放行。
- [放置位置决策] policy.json + scripts/policy-lint.mjs 放 **quant-dashboard** 侧：①原则本体是「展示策略」，看板是渲染端与规则重心；②dashboard package.json 为 type:module，.mjs 天然契合且已有 scripts 先例；③BFF 侧零改动（连 package.json 都不动），满足「零 BFF 运行时行为改动」最严格解释；④lint 经 `../quant-bff/` 相对路径只读访问 BFF 数据/源码。

## 交付物

- tools/quant-dashboard/policy.json：metrics-display-policy@v1（白名单/引擎禁用字段/口径映射 current_curve_column=F1_quarterly）
- tools/quant-dashboard/scripts/policy-lint.mjs：四检查零依赖，--dash/--bff 可选参数供自测；违规清单输出 + exit 1
- 接线：quant-dashboard/package.json scripts."lint:policy"；新建 README.md（项目原无 README）补用法行
- 放置理由：原则本体是展示策略，看板为渲染端规则重心；dashboard type:module 契合 .mjs；BFF 侧零改动（连 package.json 不动）

## 验证记录（两次输出）

【基线】node scripts/policy-lint.mjs → exit 0：
PASS — metrics-display-policy@v1；✓① engines.json+enginesHandler 无绩效字段 ✓② column=F1_quarterly+警示在场 ✓③ ablation 无绩效（免责行放行）✓④ perf-history 无硬编码（透传放行）

【破坏性自测】/tmp/policy-selftest 构造样本（engines.json 注入 sharpe:1.23；Candidates.jsx ablation 注入 <th>年化</th> 且剥离 cand-warn-line/cand-badge-warn；perf-history.js 注入 sharpe: 1.43 字面量）→ exit 1，4 项违规全部命中：
✗[①] 条目 A 含禁用 "sharpe"(1.23)；✗[②] 未找到近似口径警示渲染；✗[③] :330 表头含 "年化"；✗[④] :65 硬编码绩效数值。样本已删除。

## 自检

- 零新依赖；BFF 运行时零改动（未改 BFF 任何文件）；前端零行为改动（仅加 lint/README/policy.json/package.json script）
- performance.json/engines.json 等数据文件只读 ✓
