# task-0585 过程笔记（vC-0 权威口径供给管道）

## 0. 路径勘误（相对任务书）
- live/data 实际位于 tools/quant-bff/live/data/（nav_curves.csv 23721B，2013-08..2026-07，157 行含表头）
- BFF 源码 tools/quant-bff/src/{app.js 22340B, perf-history.js 6072B}
- performance.json 1619B：curve_source={file:nav_curves.csv,column:F1_quarterly}，metrics ann .135702/vol .094679/sharpe 1.4333/mdd -.090794
- policy.json 1275B：caliber.authoritative=rolling_equal_vol_58_42（已预留）、authoritative_available=false、current=f1_quarterly_50_50_static_quarterly
- Candidates.jsx 现警示文案实为「数据口径核验中（B0）」（cand-warn-line :119 + cand-badge-warn :291），非任务书转述的「近似口径（50/50 季度再平衡）」——按现场为准改

## 3. 供给切换实录
- 新通道文件：tools/quant-bff/live/data/nav_curves.authoritative.csv（156 行，md5 fa39e216f06fedbddb92740fb6482e2f）
  列：month, A, gold, F1_quarterly（旧口径对照）, VC0_EQVOL_5842_M（权威展示）, VC0_ROLLING_EQVOL_6M（滚动对照）, W_ROLL_A, W_ROLL_GOLD
- 选 CSV 独立新文件理由：nav_curves.csv 被 task-0492 基线 md5 9704a300 锁定（G3 逐位复现链），加列即破坏锁定溯源；独立文件零触碰基线
- performance.json 重写（备份 live/data/performance.json.bak-task0585）：curve_source→新文件:VC0_EQVOL_5842_M；metrics=权威四指标；cross_check_match:true（R-377 §七.3 P1 建议同步落地）；新增 authoritative_ref/comparison（rolling_6m+legacy 对照指标入档）
- perf-history.js：activeEntry 标签→'vC-0 现役（权威·等波动率 58/42）'，cross_check_match 由硬编码 null 改透传 perf.cross_check_match ?? null；detail 回退列名 F1_quarterly→VC0_EQVOL_5842_M
- policy.json caliber：authoritative=current=equal_vol_58_42_static_monthly；authoritative_available=true；current_curve_column=authoritative_curve_column=VC0_EQVOL_5842_M；authoritative_file=nav_curves.authoritative.csv；authoritative_rolling_candidate 预留滚动升版位
- Candidates.jsx：B0 警示行→cand-auth-line「✓ 权威口径（等波动率 58/42）：solver 定义日解 0.5803/0.4197 月度再平衡…」；cand-badge-warn→cand-badge-auth「权威口径（等波动率 58/42）」；文件头注释同步
- styles.css：新增 .cand-badge-auth/.cand-auth-line（teal 系）

## 4. B7 联动（policy-lint.mjs 检查②升级）
- authoritative_available=true 分支硬断言：curve_source.file≠authoritative_file 或 column≠authoritative_curve_column 或 Candidates.jsx 无「权威口径」或残留「数据口径核验中（B0）」→ 违规 exit 1
- false 分支保留原近似警示断言；PASS 行输出改为输出通道+硬断言状态
- 反向验证：临时把 current_curve_column 改回 F1_quarterly → lint FAIL(exit 1) 命中；还原后 PASS(exit 0) ✓

## 5. 验证输出汇总
- curl portfolios/vC-0 performance：metrics {ann .144394, vol .103211, sharpe 1.399, mdd -.096896}，curve 156 点（首点 1.033342/末点 5.774092）
- curl perf-history：vC-0 条目 label/cross_check_match=true 透传；detail #13 schema perf_history_detail@v1 兼容
- 前端构建：VITE_API_BASE=/quantv6 npm run build 零报错；npm test 39 assertions passed；grep quantv6 dist/assets/index-*.js 命中
- 390x844 无头（playwright chromium）：bodyScrollW=390/docClientW=390/overflowEls=0；徽标文本「权威口径（等波动率 58/42）」；指标格 年化=14.4%/波动=10.3%/夏普=1.40/回撤=-9.7%；核✓ 在场；B0 警示已消失；截图 work/task-0585-mobile-390.png、task-0585-mobile-390-card.png
- 趋势区末值 5.59 为归一化显示约定（首点=1：5.7741/1.03334=5.588；基准 5.89 同规则），非数据错误

## 6. 边界与遗留（如实）
- 权威曲线为裸双腿层（无 equity DDC/gold sma200+vol_target/货基层）；R-378 已证 gold 腿当前 paper 未建仓且 w=0，41.97% 为设计解——历史曲线口径与在役执行链的完全对齐需日频层数据，已写入 caliber.notes 与 policy.authoritative_rolling_candidate
- perf_history_index.json 的 caliber_ref 与 6 条历史线未动（各自口径自洽）
- README 更新日志与 R-379 报告随本批写入
