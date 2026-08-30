# task-0573 过程笔记（候选库页改版：趋势置顶 + 分页排序表格）

## 老看板参考定位
- 文件：`/root/.openclaw/workspace/tools/agent-dashboard/server.js`（718KB，禁全读，sed 抽段）
- 「回测趋势 · 策略 vs 基准」：L9889-9930 —— 策略实线蓝 + 基准虚线（hs300 灰 / ewmicro 琥珀），**各自区间首日=1 归一**，图例含标签与指标；加载失败显示占位说明不伪造。
- 「全版本排行 · 点表头排序 / 点版本切换」：L10310-10420 —— 四指标列点表头排序：新列默认降序、同列再点反向、当前列 ▲/▼ + accent 高亮；**缺指标永远排末尾不随方向翻转**；并列按 registered_at 兜底；点版本名联动顶部趋势选择器；无数据版本不可选置灰。

## 数据契约核对（R-342 v2.0 契约总表，L419-422）
- #12 GET /perf-history：`schema:'perf_history@v1'` + generated_at/caliber_ref/versions[]/skipped[]；索引缺失→空列表降级。
- #13 GET /perf-history/:id：`schema:'perf_history_detail@v1'` + performance{metrics,nav_curve[{date,nav}],...}；缺失→performance:null 不 503。
- api.js 已有 fetchPerfHistory / fetchPerfHistoryDetail / fmtID，够用，零改动。

## 实测数据（2026-08-30，BFF 127.0.0.1:8180，落盘 /tmp/task0573-*.json）
- versions 7 条：vC-0(active, ann_ret 13.57%) + F0_buyhold50(14.86%) / F1_equal / F3_volparity / F4_erc / F5_b50_tilt65_80 / F7a，全部 has_curve=true。
- **基准条目实存：F0_buyhold50（F0 买入持有50，iteration/historical）**——基准检测规则定为 id 匹配 /buyhold/i。
- skipped 3 条：F6 / F7b（无曲线产物）/ paper-r309（仅 7 交易日）。
- #13 实测：vC-0 与 F0_buyhold50 nav_curve 均 156 点，日期范围完全一致（2013-08-31 ~ 2026-07-31），首点 nav≈1.029（非 1），按老看板口径各曲线除以自身首值归一后叠加。
- 曲线对齐策略：以选中策略曲线日期为 x 轴，基准按 date 精确匹配取值，不插值不造端点；重叠点 <2 → 单曲线降级 + 说明。

## 实现要点
- 布局：HealthStrip → 返回条 → 元信息 → 【趋势区（置顶）】→【分页表格】→ skipped 全量可视区。
- 默认选中：status==='active' 的版本，否则 versions[0]；点表格行切换趋势并高亮行。
- 表格：每页 5 条；列 = 版本(fmtID 10) / 标签(ellipsis+核验角标) / 年化 / 波动 / 夏普 / 回撤；表头点击排序（新列降序→同列反向，▲/▼ 指示）；「恢复默认」清排序+回第 1 页+契约原序；缺指标恒排末尾；并列按 id 兜底；排序变更重置页码。
- 390 约束：table-layout:fixed + width:100% + 白空格 nowrap + 数字列 tabular-nums；ID/标签超宽 ellipsis；页控件按钮式（← x/y →）。
- 基准线：客户端从 versions[] 找 /buyhold/i 条目 → 单独调 #13 取 nav_curve 叠加（虚线灰）；缺失/无曲线/performance:null → 单曲线降级并文字说明，不伪造。

## 验证记录（2026-08-30）
- 构建：`VITE_API_BASE=/quantv6 npm run build` 零报错（44 modules，dist/assets/index-DuxMVa6o.js 201KB）；产物 `grep -rl quantv6 dist/assets/` → index-DuxMVa6o.js ✓ 注入核对通过。
- 测试：`npm test` → engine-copy assertions: 39 passed。
- 无头 390x844 抽查（scripts/t0573-headless-check.cjs，serve 8981 反代 8180 实数据）：
  - bodyScrollW=390 / docScrollW=390，无横向滚动 ✓
  - 趋势区在表格之前（compareDocumentPosition FOLLOWING）✓；默认选中 vC-0（active）✓；基准虚线（dasharray 5 4）已叠加 + 图例「策略/基准」✓
  - 表格 6 列（版本/标签/年化/波动/夏普/回撤），第 1 页 5 行，页脚「第 1/2 页 · 共 7 条 · 缺指标排末尾」✓
  - 点第 2 行 → cand-sec-cur 与行高亮切至 F0_buyhold50 ✓
  - 点「年化」→ ▼ 首行 F0_buyhold50（14.86% 最高）；再点 → ▲ 首行 F3_volparity（F3/F4 并列 9.51%，ID 兜底序）✓
  - 下页 → 第 2/2 页 2 行；「恢复默认」→ 契约原序 vC-0 首行、按钮禁用、回第 1 页 ✓
  - skipped 3 条全量渲染 ✓
- 本批改动文件：src/pages/Candidates.jsx（重写）、src/styles.css（追加 66 行增量样式）、scripts/t0573-headless-check.cjs（新增验收脚本）。api.js/App.jsx/hooks.js 零改动，零 BFF/nginx 改动，零新依赖。
- 契约缺口：无新发现（#12/#13 与 v2.0 总表一致；基准型条目无专门字段，前端以 id 含 buyhold 识别，已在代码注释与降级说明中如实标注）。
