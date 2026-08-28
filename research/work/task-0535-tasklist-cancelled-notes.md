# task-0535 过程笔记：任务列表「已取消」独立栏目

## 结论
已完成并通过验证。任务列表新增「已取消」独立栏目：置底、排序最后、默认折叠（点「查看更多 5 条」展开）；cancelled 任务（0520/0522/0523/0524/0525）全部移入，不再混入「待办」列；其余任务展示与排序逐张一致未受影响；API 数据结构零改动。

## 改动文件
- `tools/agent-dashboard/server.js`（唯一改动文件，diff 13 行 / 5 处 hunk，均带 task-0535 注释）
- 备份：`tools/agent-dashboard/server.js.bak-task0535-20260828`（718178 字节，改前原样）
- 截图：`tools/agent-dashboard/task0535-390x844.png`（首屏）、`task0535-390x844-cancelled-open.png`（已取消列展开态）

## 改动点（对照备份 diff）
1. L7344：状态筛选下拉末尾加 `<option value="cancelled">已取消</option>`（cancelled 排所有状态之后）
2. L8317：`renderTaskBoard` cols 增加 `cancelled:[]`
3. L8324：路由 `else if (t.status === 'cancelled') cols.cancelled.push(t)`（原走 else 混入待办）
4. L8334-8335：列 HTML 末尾追加 `taskColumn('已取消','cancelled',…)` —— 移动端 flex-column 即置底
5. L8341-8352：cancelled 列 `visibleLimit=0`（默认折叠）；`hiddenHtml` 对 cancelled 预渲染（修复懒渲染置空 bug）

## 开发中发现并修复的 bug
初版仅设 visibleLimit=0，实测点「查看更多」展开后卡片空白：现有懒渲染 `toggleTaskMore` 假设前 limit 条已可见、只渲染 `slice(limit)`，limit=5 时 `slice(5)=[]`。修复：cancelled 列改预渲染（hiddenHtml 直接渲染全部），折叠仅靠 `display:none`；`toggleTaskMore` 的 `!hidden.innerHTML` 条件自动跳过懒渲染，该函数零改动。

## 验证记录（命令与输出摘要）
1. 语法：`node --check server.js` → SYNTAX_OK
2. API（改前快照 `/tmp/task0535-tasks-before.json`）：total 457，done=450 / cancelled=5 / running=1 / rejected=1；cancelled = 0520/0522/0523/0524/0525
3. 渲染对照（`/tmp/task0535-render-check.js`：从备份与新 server.js 各抽取渲染函数跑同一份 API 数据，桌面视口）：
   - 改前待办列 = 恰好 5 个 cancelled（证明混入问题）；改后待办 = 0
   - cancelled 全在「已取消」列、无他状态混入、其他列零泄漏（A1/A2 true）
   - 除「待办」外各列（进行中/待审核/已完成/已拒绝/失败终态）卡片归属+顺序逐张一致（A3 唯一差异列=待办，即本次预期改动）
   - 列顺序：待办→进行中→待审核→已完成→已拒绝→失败(终态)→已取消，末位=已取消（A4）
   - 默认折叠（「查看更多 5 条」、可见区无卡片，A5）；展开后恰为 5 个 cancelled 任务（A6）
4. 真实页面 playwright（390x844 viewport，`google-chrome` headless）：
   - 折叠态 scrollW=390（无横向滚动）；7 列齐全、已取消 cnt=5
   - 点展开 → 卡片恰为 ['task-0520','task-0522','task-0523','task-0524','task-0525']，scrollW 仍 390
   - 再收起 → 按钮恢复「查看更多 5 条」，scrollW 390
5. 服务：`systemctl restart agent-dashboard.service`（确认单元名后 restart，非 stop+start）→ active；`GET /api/tasks?status=cancelled` 正常返回 5 条；页面 `GET /` 正常出主应用 HTML

## 备注（范围外观察，未改动）
- `.badge.cancelled` 徽章为红色（既有 CSS L6740 与 failed 同组），非本次范围
- 390px 下顶栏筛选下拉贴边、卡片内长 UUID/长标题截断为既有样式行为，本次未触碰任何 CSS
- paused 任务仍混在待办列（既有行为，需求只涉及 cancelled）
