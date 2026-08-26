# task-0499 (R-321) 前端可视化模块级精简方案 — 过程笔记

任务：R-320 增补——活 UI 可见模块的重叠矩阵与视图合并设计（纯方案，零代码改动）
看板：tools/agent-dashboard/server.js (825KB / 14942 行，只准 grep/awk 取证)

## 计划
1. 读 R-320 报告 + task-0498 笔记（背景）
2. 逐 Tab 定位 loader 行区间内 render 函数 / innerHTML 段，列可见模块清单
3. 归类信息维度 → 重叠矩阵（净值趋势类/指标卡类/版本列表类/持仓交易类）
4. 死岛（loadModelsQuant/loadBtlcQuant）功能盘点 → 复活评估
5. 写合并方案 + 文字版效果图 + 实施衔接
6. 交付报告 + .task-completions.jsonl + 回写任务状态

## 背景摘要（来自 R-320，待补细节）
- 六子Tab：data/factor/v5model/v5btlc/paper/v5hist
- 死 UI 岛：loadModelsQuant L11377-11885、loadBtlcQuant L11887-12830（P0 删除）
- 近期变更：R-315 生命周期折叠+影子趋势前置、R-313 gold 呈现、R-319 F6 模块刚上线（红线：不动在役）

## 取证记录

### T1. v5model Tab（loadV5ModelQuant L9658-9755）模块清单
| 模块 | 组件函数 | 端点 | 行区间 |
|---|---|---|---|
| M1 版本选择器 | v5VersionSelHtml L9613（模型/回测共用，task-0349） | version-options | L9613-9639+9703 |
| M2 头卡（版本名+ACTIVE/历史徽章+数据源角标+策略一句话） | renderV5Model | active?v= | L9698-9723 |
| M3 指标卡×6（年化/回撤/夏普/卡玛/月度胜率/月换手）+窗口chips（locked/full） | v5MetricCardsHtml L9579 + v5WinChips L9599 | active.windows | L9724-9726 |
| M4 模型解释三层卡（选股/择时/交易） | v5ExplainHtml L9640 | active.explanation | L9727-9729 |
| M5 择时仓位趋势图（月度仓位系数线图） | v5DrawPos L9732 | active/pos | L9730-9755 |

注：指标卡组件 v5MetricCardsHtml 是共享件（v5btlc 也会用）→ 指标卡类重叠的第一现场。

### T0. 顶部横件（量化页全局）
| 模块 | 函数 | 端点 | 行 |
|---|---|---|---|
| 数据更新条（🔄 生成时间/同步/版本数） | loadQuantFreshness | freshness | L9389-9403 |
| 一致性自检状态点（绿/黄/红，点开明细） | loadQuantConsistency + renderQuantConsistDot/Detail | consistency | L9405-9440 附近 |

### T2. v5btlc Tab（loadV5BtlcQuant L9756-10409）renderV5Btlc L9829 自上而下模块
| # | 模块 | 组件函数 | 数据源 | 行 |
|---|---|---|---|---|
| B1 | 引擎评估指标徽标行（每引擎年化/回撤/Calmar/corr 来源） | v5EngineEvalFrontHtml ① | engines.evals（A类回退versionOptions.windows） | L9921-9965 |
| B2 | 影子回测趋势对比图（A2+gold 同图，月度化，首月=1） | v5EngineEvalFrontHtml ② | engines + engines/:id/shadow-nav | L9966-10011（内联script重放） |
| B3 | F6 组合回测趋势图（F6主线/A单独/gold单独/a_dd/F1/F7/指数虚线） | v5F6CurveHtml（R-319/task-0497） | f6-curves?indexes=hs300,szzs&f7=1 | L10014-10066 |
| B4 | 版本选择器（与 v5model 共用组件） | v5VersionSelHtml | version-options | L9835 |
| B5 | 指标卡×6 + curveWin 窗口chips（与 v5model 同组件同源 active.windows） | v5MetricCardsHtml | active?v=/curves.strategy_metrics | L9838-9841 |
| B6 | 回测趋势·策略vs基准净值图（全期/3y/1y chips） | v5DrawNav L10330 | active/curves?v= | L9842-9861 |
| B7 | 全版本排行表（四指标排序，点击联动版本选择器） | v5RankTableHtml L10265（task-0382） | version-options | L9862 |
| B8 | 引擎级生命周期折叠面板（默认折叠；引擎切换器+因子模型卡+生命周期层+迭代轨迹散点） | r315LcPanelHtml L9887 / v5EngineSwitcherHtml L10187 / v5EngineRegionHtml L10204 / v5EngineFactorModelBlock L10139 / renderLifecycleLayer L13139 / drawLifecycleScatter L13082 | engines+lifecycle+registry | L9863-9867 |

关键重叠证据（趋势图类）：
- A 引擎（a13 现役）净值曲线出现于：B6（策略vs基准主图）；F6 图中「A单独(a_alone)+A降仓(a_dd)」序列（B3，月频口径）；paper Tab 需查。
- gold 净值出现于：B2（gold 影子）；B3（gold_alone 序列）；paper Tab 需查。
- 指数叠加（沪深300/上证）出现于：B3 F6 图（indexes 参数）；B6 v5DrawNav 需查 datasets；paper Tab 需查。
- B2 图脚注原文（L10003 附近）：「注：A 引擎（a13）等价长回测 nav 未并入本图，见下方『回测趋势 · 策略 vs 基准』」→ 设计者已知分段问题。
- 指标卡类：v5MetricCardsHtml 被 v5model(M3)+v5btlc(B5) 同组件复用，同源 active.windows；B1 徽标行的 A 引擎年化/回撤/Calmar 又取 versionOptions.windows = 第 3 处。
### T3. v5hist Tab（loadV5HistQuant L10410-10602）
| 模块 | 函数 | 端点 | 行 |
|---|---|---|---|
| H1 迭代历史分页列表（每行：版本+徽章+locked 年化/回撤/夏普+features+最近决策） | renderV5HistList | history?page | L10435-10479 |
| H2 legacy 隐藏开关 | v5ToggleLegacy L10400 | — | L10445-10449 |
| H3 详情抽屉（报告式弹层）：选股参数/Gate评估(verdict+holdout段指标)/Locked指标卡×6/Full指标卡×6/机制解释/决策记录 | v5OpenHist+v5LoadHistDetail+renderV5HistDetail | history/:vid | L10468-10602 |

重要：H3 详情含「Gate 评估」区块（L10539 附近 section-title 'Gate 评估' + verdict + holdout segment 年化/回撤/夏普）→ 死岛 gates 端点的 verdict 类信息在活 UI 已部分覆盖（版本粒度）。v5MetricCardsHtml 第3/4处复用（locked+full 两套卡）。

### T4. data Tab（loadDataQuant L10603-10749）
| 模块 | 函数 | 端点 | 行 |
|---|---|---|---|
| D1 数据健康校验卡组（checks PASS/FAIL + 4 灰卡：财务新鲜度/估值新鲜度/PIT/幸存者偏差，graycards_cache 回退灰卡） | renderDataQuant a) | data-health | L10637-10694 |
| D2 数据资产盘点表 | renderDataQuant b) | data-assets | L10696-10748 |

### T5. factor Tab（loadFactorQuant L10750-11376）
| 模块 | 函数 | 端点 | 行 |
|---|---|---|---|
| F1 类型 Tab 栏（9类+全部，角标 n达标/n测试） | renderFactorTypeTabs | factor-catalog | L10874-10892 |
| F2 因子注册表（M1.2，分组折叠表，14列，行展开36月IC图📈） | renderFactorRegistry + onFactorExpand L11000 | factor-catalog + factor-ic-series | L10893-10982 |
| F3 在役因子 IC 监控（M1.3，月度IC多线图+模式切换） | renderFactorIcMonitor + loadIcMonitorChart | factor-ic-series×n + data-health | L11055-11246? 待精确 |
| F4 因子相关性簇（M1.4，簇折叠卡） | renderFactorClusters | factor-catalog | L11132-11188? 待精确 |

**活 UI 内死代码簇（重大发现 #1）**：
- renderFactorTable (L11247-11322) 被注释「M1.2 核心重构：替换 renderFactorTable」→ 新版 renderFactorRegistry 上位。旧链 buildMergedFactorSummary L11189/factorRowsFromSummary L11211/factorFilterRows L11231/renderFactorTable L11247/onFactorSearch L11323/onFactorPage L11227/factorTableRoot L11317 依赖 DOM id=factorTableRoot（新版 DOM 是 factorRegistryRoot）→ 整链死代码（~190 行）。
- renderFactorIcChart L11348-11375 零调用（grep 仅定义行）→ 死函数。
- **附带功能 bug 实锤**：新版 renderFactorRegistry 分组头 onclick=onFactorGroupToggle（L10927）→ onFactorGroupToggle L11330 只更新 factorTableRoot（不存在）→ 点击新版分组头：状态翻转但无重渲染，折叠功能静默失效（除非 root 存在）。P0 删除时应把 onFactorGroupToggle 重写为更新 factorRegistryRoot 或触发 loadFactorQuant(force)。
### T6. paper Tab（loadPaperQuant L13152-13743，renderPaperQuant L13744-13912）自上而下模块
| # | 模块 | 组件函数 | 数据源 |
|---|---|---|---|
| P0 | paper↔active 行为一致性徽标（task-0352） | 内联 | paper/summary.rules_align |
| P1 | 策略描述行（动态闸门拼装 task-0387） | quantSelDescParts | registry/evolution/models |
| P2 | 指标卡×6：当前净值/累计收益/当月收益/下次调仓日/运行天数/持仓数 | 内联 stat-card | paper/summary |
| P3 | 运行状态条（产物 mtime 红绿灯） | renderRunStatusBar L13237 | run-status |
| P4 | 净值曲线（择时仓位双轴或纯净值） | renderNavWithPosChart L13507 / renderNavChart L13987 | paper/nav + timing |
| P5 | 跨引擎影子卡（每影子引擎一张：影子NAV vs parent在役NAV 双线；gold 单线+激活徽章+paper 实时小区块） | renderCrossEngineShadowCard L13574（R-259/R-313） | engines + engines/:id/shadow-nav + engines/:id/paper + active/curves |
| P6 | 当前持仓可解释表（入选理由展开+组合概览） | renderHoldingsExplainable L13294 | paper/portfolio + summary |
| P7 | 最近交易记录表 | 内联 | paper/trades |
| P8 | 运行模型版本卡（registry active 一致性徽章+择时层状态） | 内联 | evolution/models + registry |
| P9 | 微盘拥挤度卡 | renderCrowdingCard L13379 | crowding |
| P10 | 退出纪律卡 | renderRiskCharterCard L13469 | risk-status |
| P11 | 策略参数&采纳因子 | renderAdoptedFactors L7510 | evolution/models |

paper loader 并行拉 16 类数据（L13166-13205）：paper四件+models+baseline/summary?version+run-status+crowding+risk-status+registry+timing+engines(→每影子引擎 shadow-nav+paper)+active/curves。
**关键：active/curves 在 v5btlc(B6) 与 paper(P5 parent线) 双拉；registry 在 v5btlc/paper 双拉；engines 在 v5btlc(2次)/paper(1+n) 多拉。**

### T7. 死岛 A（loadModelsQuant L11377-11885，quant-page-models 无入口）模块清单（供复活评估）
| 模块 | 函数 | 独占端点 |
|---|---|---|
| A1 当前生效·作战室控制面 | renderActiveOverviewCard L11422 | —（registry/paper-summary） |
| A2 决策时间线（ADR） | renderDecisionTimeline L11485 | decisions |
| A3 Pending 确认（人工决策点） | renderPendingConfirm L11527 | pending |
| A4 想法池（ideas 入口+提交按钮） | renderIdeasPool L11604 | ideas |
| A5 试验台账（n_trials 过拟合治理） | renderLedger L264→L11642 | ledger |
| A6 择时版本×SOTA选股 贡献矩阵 | renderTimingContributionMatrix L11718 | timing-matrix |
| A7 选股模型（Alpha层） | renderModelsQuant L11764 内 | — |
| A8 择时模型（仓位层）+择时仓位系数图 | 同上 | timing-config |
| A9 报告库入口卡 | L11388 | reports（列表） |
| 动作链 | quantEnqueueAction L11685（rollback/confirmPending/rejectPending/submitIdea） | POST action + action-queue |

### T8. 死岛 B（loadBtlcQuant L11887-12830，quant-page-btlc 无入口）模块清单
| 模块 | 函数 | 独占端点 |
|---|---|---|
| B'1 版本切换器+四层归因链（版本绑定同口径） | renderBtlcAttributionChain | btlc |
| B'2 端到端vs基线对照（M3.1）+净值对比图（M3.2 危机底色） | renderBtlcNavChart | btlc |
| B'3 分年度收益（M3.3 基线+沪深300+超额） | renderBtlcYearly | btlc |
| B'4 危机段回撤实测（M3.4） | renderBtlcCrisis | btlc |
| B'5 Walk-forward 样本外（M3.5 三窗OOS） | renderBtlc 内 | btlc |
| B'6 历代最优对比（M3.6 过拟合直觉化） | renderBtlcGenerations L12190 | btlc |
| B'7 报告库（M3.7 代际分组+搜索） | renderBtlc L12239 附近 | reports |
| B'8 E2E 多版本净值对比+指数叠加（5指数可选） | btlcE2E* L12251-12445 | e2e-curves |
| B'9 基线卡（版本切换） | loadQuantBaselineCard L12446 | models + baseline/meta |
| B'10 模型层·版本切换器（选股/择时版本列表+WF/DSR 摘要） | loadQuantModelLayer L12656 | models |
| B'11 验证层·五门禁面板 + DSR 折扣曲线（示意阶梯）+ A/B/C/BUB 口径对照 | loadQuantValidationLayer L12729 + renderValidationLayer L12741 + drawDsrCurve L12801 | gates + dsr + q4b-contrast |
| B'12 生命周期层薄壳 | loadQuantLifecycleLayer L12836 | lifecycle（活版 renderLifecycleLayer 被 v5btlc 用，仅薄壳死） |

### T9. e2e-curves 归属修正（对任务描述的修正）
任务描述称「loadV5BtlcQuant …含 e2e-curves 死调用」——实测 grep e2e-curves 前端消费点全部位于 L12251-12445（死岛 B btlcE2E* 系列），v5btlc 段（L9756-10409）零引用。e2e-curves 属死岛 B 独占（与 R-320 结论一致）。
openQuantReportDetail L14029 全部 4 个调用点（L12205/12239/12598/12599）均在死岛 B → reports/:id 亦死树独占（R-320 报告正文口径正确，notes E4.2「活」为早期误记，E10/E11 已修正）。

### T10. qLifecycleShadow（v5btlc B8 内）内容确认
L12952：影子观察中（shadow_watch）进度卡——版本级：每版本 clean_evals 进度（第N/需M期）+since+note。与 paper P5 影子卡（引擎级 NAV 曲线+paper 实时）粒度不同：B8=版本级观察进度，P5=引擎级曲线对照。信息有交集（clean_evals 进度两处都出现：P5 影子卡脚注也含 clean_evals 进度，R-320 notes 已记）。

### T11. 死岛端点数据源活跃度（决定复活/埋掉）
- btlc 端点（L4575）：btlcResolveLayers L4270 + btlcBuildYearly L4401 + btlcBuildCrisis L4433 + btlcBuildGenerations L4487 均**动态计算**，读 model/main.json 真源（QUANT_MODEL_DIR=/root/.openclaw/workspace-quant/model，L3579）→ 深度分析（分年度/危机/WF/历代最优）有数据支撑，非死数据；但 v5btlc 活页只展示总量指标+净值曲线，未展示这些深度分析 → **独有信息，是否复活待评估**。
- gates 端点（L2915）：读 results/model/v0_seed.json（MODEL_REGISTRY_DIR L2853，8月16日文件）→ 绑定旧周期 v0_seed 基线「无候选裁决」中性态 → **死数据**。
- dsr 端点（L2943）：同理 v0_seed 系；drawDsrCurve L12801 的「示意阶梯」是硬编码假数据（L12806-12816 常量步骤 0.90→0.93→0.95）→ 非实时。
- reports 列表（L2143）：读 QUANT_REPORTS_DIR=workspace-quant/results 下 .md，实测仅 3 个历史 md（a7-iteration-report / factor-expansion-report / R-188-quant-evolve-Phase1）→ 非活跃产出。
- q4b-contrast（L2870）：Q4B 一次性研究池对比 → 研究产物。
- e2e-curves（L4689）：读 timing_iter3 CSV（已不存在，R-320 E4.6 僵尸）→ 确认死。

### T12. 复活评估结论（定稿）
- 高优先复活：**无**。决策/台账/裁决/gate verdict 核心信息活 UI 已全覆盖（B8 生命周期层 + H3 详情 Gate 评估 + B8 影子观察）。
- 可选复活（P1.5/P2，低优先，均需用户拍板）：
  1. gate 明细折叠：H3 详情「Gate 评估」区扩展为五门禁 g1-g5 逐项（数据源改 lifecycle/registry 真源，不沿用 gates 端点旧 v0_seed）。不复活也损失不大（verdict 已在）。
  2. DSR 文本摘要：B8 台账区加一行「DSR 门槛 ≥0.95 @174 trials」文本（不画曲线——示意阶梯是硬编码假数据）。
  3. 报告原文链接：v5hist 详情抽屉加 md 报告查看（保留 openQuantReportDetail 组件 + reports/:id 端点）。当前 reports 仅 3 个历史 md，价值低。
- 随死岛埋掉：A1-A9（含 A6 择时矩阵——timing_matrix 数据无消费方）、B'1-B'6（归因/年度/危机/WF/历代最优——深度分析虽动态但 v5btlc 已定位为「总览页」，深度分析属研究回顾，埋掉后可随 P2 按需在 v5hist 详情补）、B'7-B'12、q4b、e2e、DSR 曲线、五门禁面板（v0_seed 死数据）。

### T13. 重叠矩阵核心数字（供报告引用）
- A 引擎净值曲线：活 UI 3 处 = B6(active/curves 日频全期) + B3(f6-curves a_alone/a_dd 月频) + P5(active/curves strategy.full 月度化 parent 线)。+死岛 2 处(B'2 btlc、B'8 e2e)。
- gold 净值：活 3 处 = B2(shadow-nav gold) + B3(gold_alone) + P5(gold 卡+paper 实时)。死岛 0。
- A2 净值：活 2 处 = B2 + P5。死岛 0。
- 指数叠加(hs300/szzs)：活 2 处 = B6(hs300 线) + B3(hs300+szzs 虚线)。死岛 2 处(B'3 年度表基准列、B'8 e2e 5指数)。
- 指标数字(年化/回撤/Sharpe/Calmar)：活 9 个渲染点 = M3卡 / B1徽标行 / B5卡 / B3脚注 / B7排行表 / H1行内 / H3 locked卡 / H3 full卡 / B8台账+散点。同源(active.windows/engines evals/version-options windows)至少 6 处。
- 版本全量列表：3 处 = M1/B4 下拉(交互控件,非冗余) + B7 排行表(version-options) + H1 分页列表(history)。数据源 2 个。
- 影子观察进度(clean_evals)：2 处 = B8 qLifecycleShadow(版本级,lifecycle) + P5 影子卡徽标(引擎级,engines evals)。
- 仓位系数：活 2 处 = M5(active/pos 独立图) + P4(paper/nav+timing 双轴)。死岛 A8 1 处。
- 决策记录：活 2 处 = B8 qLifecycleTimeline(全局) + H3 详情(单版本)。死岛 A2 1 处。
- 持仓/交易：仅 P6/P7 各 1 处，无重复。
- 因子展示：3 粒度 F2(全库) / P11(在役采纳) / B8(引擎绑定)，无实质重复。

### T14. 端点跨 Tab 重复拉取
- registry：v5btlc + paper
- active/curves：v5btlc(B6) + paper(P5 parent 线)
- engines：v5btlc(loader 内 2 次) + paper(1 主拉 + 每影子引擎 shadow-nav+paper 共 2n)
- version-options：v5model + v5btlc
- shadow-nav：v5btlc(B2) + paper(P5)
- data-health：data + factor(F3)
→ 同会话切换 Tab 重复拉取同一端点，建议 P1.5 会话级缓存（TTL 30s）。
