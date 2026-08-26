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

