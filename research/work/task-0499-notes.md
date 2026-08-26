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
