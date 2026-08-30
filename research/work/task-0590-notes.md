# task-0590 工作笔记（B10 徽标同源化+滚动对照挂出+lint 血缘断言）

## 实查事实（2026-08-30）

### 数据源定位
- 看板根：/root/.openclaw/workspace/tools/quant-dashboard/
- policy.json：看板根（1676B），lint 与（将）被 JSX 构建期 import
- performance.json：tools/quant-bff/live/data/performance.json（3226B，数据文件只读约束）
  - curve_source.column = VC0_EQVOL_5842_M，file = nav_curves.authoritative.csv，md5 = fa39e216f06fedbddb92740fb6482e2f
- nav_curves.authoritative.csv：18429B，157 行（156 月），表头：
  `month,A,gold,F1_quarterly,VC0_EQVOL_5842_M,VC0_ROLLING_EQVOL_6M,W_ROLL_A,W_ROLL_GOLD`
  - 实测 md5 = fa39e216f06fedbddb92740fb6482e2f（与 performance.json 记录一致 ✓）
- API 链路：/api/v1/portfolios/vC-0 与 /api/v1/perf-history/vC-0 都返回 `{...performance.json 全文, nav_curve}` → **curve_source 已透传到前端**（Version.jsx PerformanceSection 可直接用 perf.curve_source）

### 徽标字面实查
- 「权威口径（等波动率 58/42）」字面在 **Candidates.jsx** 两处：L119（cand-auth-line 警示行）、L291（cand-badge-auth 徽标）。任务书说 Version.jsx，实查在 Candidates.jsx —— 两文件都按同源派生改。
- BFF perf-history.js activeEntry 有硬编码 fallback label「vC-0 现役（权威·等波动率 58/42）」（performance.json 无 label 字段 → fallback 生效，该文本经 /perf-history 流到候选卡 cand-label）。
  - 处置：BFF 代码不在交付物清单且改 BFF 需重启服务（未授权）→ 前端 Candidates.jsx 对 active 卡渲染时用 policy 派生文案覆盖 v.label；lint 增断言 JSX 不含「权威口径（等波动率」且含覆盖逻辑。BFF 残留 fallback 在报告中如实说明。

### 滚动对照数字复核（python 实算 VC0_ROLLING_EQVOL_6M 列，156 点，2013-08-31..2026-07-31）
- 方法 A（与主曲线同法：基期 1.0，ann=(末值)^(12/156)−1）：ann = 0.1011730 → 10.12% ✓；mdd（含基期峰值法）= −0.0570666 → −5.71% ✓
- 与任务书给定 ann 10.12% / mdd −5.71% 吻合 → policy.rolling_compare 记 {ann:0.1012, mdd:-0.0571}，lint 用同法重算比对（容差 1e-4）

### lint 现状（scripts/policy-lint.mjs，四检查）
- ①引擎层禁令 ②口径标注（authoritative_available=true 分支硬断言；false+approx_label_required=true 分支要求近似警示）③ablation 绩效禁令 ④perf-history 硬编码指标禁令
- 改后 authoritative_available=false 且 approx_label_required=false → 原②两分支都旁路 → 必须新增 false 分支语义：display_name 必须存在、JSX 必须引用 policy 派生、「权威口径（等波动率」字面必须不存在

## 改动方案
1. policy.json caliber：current=static_5842_monthly_rebalance_proposal；+display_name；+hindsight_attribution_pending:true；authoritative_available→false + authoritative_available_note；+rolling_compare{file,column,ann,mdd,label,note}；authoritative 定义字段保留
2. Candidates.jsx：import policy.json（Vite 构建期内联，零新依赖）；徽标+警示行文案从 CAL.display_name 派生；active 卡 label 用 policy 派生覆盖；vC-0 卡加滚动对照行（全字段来自 policy）
3. Version.jsx：PerformanceSection 加同源口径行（perf.curve_source.file:column + CAL.display_name）+ 滚动对照行
4. policy-lint.mjs：②改语义 + ⑤血缘断言（CSV 表头实读比对 curve_source.column 与 rolling_compare.column；md5 比对；滚动 ann/mdd 重算比对；JSX display_name/rolling_compare 引用断言；旧字面禁令）
5. styles.css：徽标长文案 390 防横滚（待查现类样式后定增量）

## 验证记录
（待填）
