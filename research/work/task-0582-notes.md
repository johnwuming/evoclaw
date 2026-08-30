# task-0582 过程笔记（B1 止血：候选库重构）

## 数据事实（2026-08-30 13:40 实测 GET /api/v1/perf-history，BFF 8180，落盘 /tmp/t0582-perf.json）
- versions 7 条：vC-0(active,label='vC-0 现役（F1·vc0 口径）')、F0_buyhold50(historical,基准)、F1_equal/F3_volparity/F4_erc/F5_b50_tilt65_80/F7a(均 historical)
- skipped 3 条：F6/F7b（无曲线产物）/paper-r309（真实盘仅7交易日）——本无绩效，不动
- metrics 字段：ann_return/ann_vol/sharpe/max_drawdown；cross_check_match: true/false/null
- 构建方法已在 label 内：等权/波动率平价/ERC/基50倾斜65/80/DDC减仓 → ablation 列表直接用 label，无需另造映射

## 分类逻辑（前端判定，零 BFF 改动）
- 主区 = status==='active'（vC-0）∪ id 含 buyhold（F0_buyhold50）→ 两张卡展示完整指标
- ablation 区 = 其余 versions（F1/F3/F4/F5/F7a）→ 折叠区，仅 名称/方法标签(label)/核验标记/状态，无指标列

## 测试安全
- npm test = scripts/engine-copy.test.mjs，39 断言只测 src/engineCopy.js，不 import Candidates.jsx → 重构无影响
- t0575-headless-check.cjs 模式：playwright-core @ pnpm 全局路径 + chrome-headless-shell，goto 127.0.0.1:8981（t0578-static-server）待复用

## 改动方案（Candidates.jsx + styles.css）→ 已落地 13:50
1. ✅ 主区「组合模型与基准 · 绩效指标」：2 张指标卡（vC-0 带 cand-badge-warn 徽标 title=task-0581；F0 蓝色基准卡不可点选）；MetricGrid 4 格年化/波动/夏普/回撤；点卡切换趋势选中
2. ✅ 趋势区不动；CandTrend 增 warn prop：选中现役时顶部琥珀警示行（口径核验中 B0）
3. ✅ 「构建层 ablation 对照（不含绩效，仅逻辑/状态）」<details> 默认折叠：版本/构建方法/核验/状态 4 列 + 底部说明「不含绩效指标」；排序/分页/RANK_COLS/cmpMetrics 整体移除
4. ✅ skipped 区不动；分类=status==='active' ∪ id含buyhold，其余→ablation

## 验证（全部通过，14:25）
- [x] VITE_API_BASE=/quantv6 npm run build 零报错（44 modules，dist/assets/index-D16lyTxZ.js）
- [x] npm test：engine-copy assertions: 39 passed
- [x] grep -rl quantv6 dist/assets/ → dist/assets/index-D16lyTxZ.js 命中
- [x] 390 无头（scripts/t0582-headless-check.cjs + t0578-static-server 复用）→ T0582 CHECK PASS：
  bodyScrollW=390/docScrollW=390；主区恰 2 卡（● vC-0、F0_buyhold50）各 4 指标格；
  vC-0 徽标「数据口径核验中（B0）」在场且 title 含 task-0581；趋势 svg+虚线基准+警示行在场；
  ablation 默认折叠（open=false 且内容 checkVisibility=false），展开后表头仅 版本/构建方法/核验/状态，无绩效表头、行内无指标值泄漏，5 行；skipped 3 条
- 注：折叠可见性探测历经 3 版（computed display→offsetHeight→checkVisibility），headless chromium 对 closed details 用 content-visibility 隐藏，前两者误报，最终用 checkVisibility()

## 改动文件清单
- src/pages/Candidates.jsx（重写主区/ablation；趋势/skipped 保留）
- src/styles.css（末尾 cand-0582 增量 ~40 行）
- scripts/t0582-headless-check.cjs（新增验收脚本）
- 零改动实证（mtime）：Version.jsx 08-30 13:13（spawn 前）、App.jsx/hooks.js 06:55、api.js 08-29；BFF 零改动
