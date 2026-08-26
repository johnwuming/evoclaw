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

