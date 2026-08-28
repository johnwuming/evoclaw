# task-0535 过程笔记：任务列表「已取消」独立栏目

## 现状勘查（改前）
- server.js 718KB（>30KB 禁全读，全部用 sed/grep 定点取段）
- `renderTaskBoard`（约 L8311）：按状态分组 cols = pending/running/review/done/rejected/failed_final；
  **cancelled 走 else 分支混进「待办」列**（paused 也混在待办，本次不动）
- `taskColumn`（约 L8340）：移动端 visibleLimit=5、桌面 10，超限走「查看更多 N 条」懒渲染，
  展开状态存 `window._expandedCols[statusKey]`
- 状态筛选下拉 `#taskStatusFilter`（约 L7335）：无 cancelled/paused 选项
- 状态中文映射 TASK_STATUS（L7594）已含 `cancelled:'已取消'`，badge/card CSS 已有 cancelled 样式（L6740/6781）
- 改前 API 快照：/tmp/task0535-tasks-before.json —— total 457；
  分布 done=450, cancelled=5, running=1, rejected=1；
  cancelled = task-0520/0522/0523/0524/0525 ✓（与任务书一致）

## 改动方案（纯展示层，不动 API）
1. `renderTaskBoard`：cols 增加 `cancelled:[]`；路由 `else if (t.status === 'cancelled') cols.cancelled.push(t);`（置于 else 之前）
2. 列 HTML 末尾追加 `taskColumn('已取消', 'cancelled', cols.cancelled)` —— 列序排最后（移动端 flex-column 即置底）
3. `taskColumn`：`cancelled` 列 visibleLimit=0 → 默认全折叠，按钮「查看更多 N 条」展开（复用现有懒渲染+展开状态记忆机制，零新增 JS 分支）
4. 筛选下拉末尾加 `<option value="cancelled">已取消</option>`（cancelled 在所有状态之后）
