2026-08-30 20:42:50 task-0591-dev 启动：④lint⑥重算血缘 ②滚动四指标 ③PRD演进目标化。已确认 B8 引擎语义：首月建仓成本 0.0013 在场、月度漂移Δw成本、pct_change 首行相对基期1.0、产物 round(10)。

## ④ lint检查⑥ 重算血缘断言（已完成）
- 关键对齐发现（任务书「首期建仓免成本」表述与 B8 实际引擎不符，按任务书要求以 B8 引擎为准）：task-0585-compute_vc0_authoritative.py run_engine 首月 cost=0.0013×(|wA|+|wG|)=0.0013 在场（产物首点 1.0333423802 = 无成本值 1.0346423802 - 0.0013，逐位验证）；此后每月 cost=0.0013×(|目标-上月漂移权重|)，月度再平衡月月有漂移；首行收益相对基期 1.0（pct_change.fillna(A-1)）；产物列 round(10)。
- Python 原型复现：156 点 max_rel_err=4.075e-11 < 1e-10 ✓（残差=round(10) 噪声+浮点序差）。
- policy.json 新增 caliber.static_recalc{source_file:nav_curves.csv, w_a:0.580297, w_gold:0.419703, cost_rate:0.0013, rel_tol:1e-10, anchor:...}——参数锚 policy，lint 零硬编码。
- policy-lint.mjs：新增 checkRecalcLineage()（月轴逐行比对/非正数值拒绝/行数比对/建仓成本在场/漂移Δw成本/逐点相对误差≤1e-10，违规文案「重算与产物失配（基底错或产物损坏）」）；⑤c 顺带升级为 rolling_compare 四指标（ann/vol/sharpe/mdd）全部声明+实算比照（TOL 1e-4）；PASS 输出增⑥行。
- 实跑：真实数据 PASS exit0（156点）；破坏性自测 /tmp/t0591-bff（全拷 live/data+src，2020-03-31 VC0 值×1.01）→ FAIL exit1，命中「⑤md5失配 + ⑥重算与产物失配 max_rel_err 9.901e-3 @2020-03-31」✓。

## ② 滚动对照四指标同构（已完成）
- 实算 VC0_ROLLING_EQVOL_6M（156点，基期1.0法，与主曲线同法）：ann=0.101173 / vol=0.066419 / sharpe=1.5233 / mdd=-0.057067。与 policy 已声明 ann 0.1012 / mdd -0.0571 相容（±1e-4）。
- policy.json rolling_compare 补 vol=0.0664、sharpe=1.5233；label/note 原文保留（走前真解·待归因，未启用）。
- Version.jsx PerformanceSection：滚动对照行改为 ann/vol/sharpe/mdd 四指标，同构主口径格式（fmtPct×3+fmtNum(2)），全部 policy.rolling_compare 派生（RC 变量），无手写字面。
- 验证：VITE_API_BASE=/quantv6 npm run build 零报错（index-DvgzRzsj.js 208.54kB）；npm test 39 passed；grep -rl quantv6 dist/assets 命中 index-DvgzRzsj.js；policy-lint PASS（⑤四指标实算一致+⑥在场）。

## ③ PRD 演进目标化（已完成，v1.4→v1.5）
- 实查：37KB 禁全读，grep 定位三处打架点——区块③三层定义（L116 构建层「现役等波动率」，未区分静态/滚动/无风控）；模块对照表「净值曲线」行（L322 仍写「待 B8 权威口径管道」，实际 B8 已落地）；修订记录止于 v1.4（早于 B8 偏离披露）。
- 改写（纯增量，v1.4 快照与两条用户落款裁定原文不动）：区块③ L116 后增补「组合构建层口径演进目标」=v1 当前（静态 58.03/41.97 月度再平衡·无风控层，R-379 上线，VC0_EQVOL_5842_M，task-0590 撤权威标签+lint⑥把守）/v2 目标（滚动真解+风控层，末端失配 26.6pp+hindsight 未排除，随 HP 日频翻转 authoritative_rolling_candidate，翻转后权威徽标恢复）/翻转前全文按 v1 理解不打架。
- 模块对照表「净值曲线」行根因/处置增量修订：B8 管道已落地（task-0585）+ 总览接线待复测 + 滚动真解走 candidate（P1）。
- 修订记录追加 v1.5 行（注明 08-30 方法偏离与 R-379/task-0590、lint⑥ 与滚动四指标同构）。错字一次（hindsight 写坏）当场修复。

## 390 无头自查（已完成）
- scripts/t0591-headless-check.cjs（新增，参照 t0590 版式）+ 复用 t0578-static-server.cjs（8981，代理 8180 BFF）。
- 结果 CHECK_PASS：bodyScrollW=390/docScrollW=390；caliberLine 原样；rollingLine=「滚动等波动率对照：ann 10.12% / vol 6.64% / sharpe 1.52 / mdd -5.71%（走前真解·待期限结构对齐与 hindsight 归因，未启用）」四指标与主口径同构且全部 policy 派生；主指标卡 4 张 14.44%/10.32%/1.40/-9.69%；无旧字面「权威口径（等波动率」。截图 work/task-0591-version-390.png。

## 修改文件清单（dev 线全部）
1. tools/quant-dashboard/policy.json —— rolling_compare 补 vol/sharpe；新增 caliber.static_recalc（⑥参数锚）
2. tools/quant-dashboard/scripts/policy-lint.mjs —— 新增检查⑥重算血缘断言；⑤c 升级四指标实比；头部注释+PASS 输出
3. tools/quant-dashboard/src/pages/Version.jsx —— 滚动对照行四指标同构（RC 变量 policy 派生）
4. shared/results/05-量化投资/R-344-Dashboard产品方案PRD.md —— v1.5：演进目标结构（纯增量）
5. tools/quant-dashboard/scripts/t0591-headless-check.cjs —— 新增无头自查
6. 过程笔记本文件

## 验证汇总（全绿）
- VITE_API_BASE=/quantv6 npm run build 零报错（index-DvgzRzsj.js）；npm test 39 passed；grep -rl quantv6 dist/assets 命中
- node scripts/policy-lint.mjs PASS 六项全过（含⑥ 156 点逐位 rel≤1e-10）
- 破坏性自测：/tmp/t0591-bff 篡改 2020-03-31 值 ×1.01 → FAIL exit1，⑤md5+⑥「重算与产物失配 max 9.901e-3」双双命中
- 390 无头 #/version CHECK_PASS（四指标在场、无横滚、无旧字面）
- 数据文件零改动（nav_curves*.csv/performance.json 只读；/tmp 篡改仅自测副本）；零新依赖；零 BFF 运行时改动
- 未新增 R-xxx 报告（本批=代码+PRD 修订；README 更新日志按「每报告一行」惯例不动，避免与并行 research 线编号冲突）

## 红线②合规微批（08-30 21:23 用户更正，从任务 notes 实查发现）
- 更正内容：PRD「当前供给」必须参数化两段式（目标态不变=滚动等波动率+风控层 / 当前供给一行可切换=静态 58/42 月度·提案轨迹），禁止写死任何口径为「权威」。
- 落实：区块③演进块改写为「v1 当前供给（一行可切换，提案轨迹）…不写死为权威」+「v2 目标态（不变）…当前供给一行切换至 v2（policy 升版），徽标随归因与频率对齐完成后再议恢复」；v1.5 修订记录行补参数化两段式说明。全文无任何当前口径被称「权威」（仅存「撤权威标签/徽标恢复再议」事实性表述）。
- 红线①（R-380 同风控配置）属 research 线范围，dev 线不涉及；红线③（lint 扫描面清单）已按 notes 同步 task-0592 第④项，本批不动。

## 用户补充要求并入验收（会话路由消息）
- 要求：③PRD「当前供给」段参数化两段式（目标态（不变）：滚动等波动率+风控层 + 当前供给（一行可切换）：静态 58/42 月度（提案轨迹））；R-380 结论翻转与否只改供给行不动目标态；禁止写死当前口径为「权威」。②④照常。
- 落实：区块③演进块头行显式写出两段式全称与「只改供给行不动目标态」规则；小节顺序改为 目标态（不变）在前、当前供给（一行可切换，提案轨迹）在后；块内「权威」仅存 2 处事实性表述（撤权威标签/不写死为权威），无任何当前口径被称权威。v1.5 修订记录行已含参数化两段式说明（此前微批已写）。
- ②（vol/sharpe 同构）与④（⑥重算血缘断言）维持已完成状态，无需改动。
