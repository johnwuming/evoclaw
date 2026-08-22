# task-0450 修复笔记：GET /api/tasks limit 参数不生效

## 目标
server.js `app.get('/api/tasks')` 处理器支持 `?limit` / `?offset`；不带 limit 时行为与历史完全一致（全量）。

## 基线（修复前，改动前实测）
- `GET /api/tasks`（落盘 /tmp/t0450-full-before.json）：count = **388**（任务书里 378 是较早数据，系统在增长）
- 全量前 6 条 id：task-0460, task-0455, task-0456, task-0457, task-0458, task-0459
  → 预期 offset=5 时首条 id = task-0459（第 6 条）
- `grep -n "ORDER BY t.created_at DESC'"`：全文件仅 1 处（第 813 行），oldText 定位唯一

## 改动 diff 摘要（server.js，仅该处理器内，813 行后新增 8 行，无删改原行）
```diff
   sql += ' ORDER BY t.created_at DESC';
+  // task-0450：支持 ?limit &offset 分页（limit 须为 1~500 整数；offset 须为 1~100000 整数且仅在 limit 生效时使用）。
+  // 非法或缺省时忽略、回退全量——不带 limit 的调用行为与历史完全一致。
+  const lim = /^\d+$/.test(q.limit) ? parseInt(q.limit, 10) : NaN;
+  if (lim >= 1 && lim <= 500) {
+    sql += ' LIMIT ?'; params.push(lim);
+    const off = /^\d+$/.test(q.offset) ? parseInt(q.offset, 10) : NaN;
+    if (off >= 1 && off <= 100000) { sql += ' OFFSET ?'; params.push(off); }
+  }
   const tasks = db.prepare(sql).all(...params);
```
设计要点：
- 严格 `/^\d+$/` 校验（拒绝 "5abc"/"5.5"/"-3"/数组参数），NaN 比较为 false → 自然落入全量分支
- OFFSET 仅在 limit 生效分支内追加 → offset 单独传无效
- LIMIT/OFFSET 参数 push 进同一 params 数组，位于 WHERE 参数之后，顺序正确

## 验证记录
- `node --check server.js` → SYNTAX_OK ✅
- （重启与接口验证见下文追加）

## 验证结果（重启 agent-dashboard.service → is-active=active 之后实测）
| # | 命令 | 实际输出 | 判定 |
|---|---|---|---|
| 1 | `?limit=5` | count=5，ids=[task-0460,0455,0456,0457,0458]（与全量前5一致） | ✅ |
| 2 | `?limit=5&offset=5` | count=5，first id=**task-0459** = 全量列表第 6 条 | ✅ |
| 3 | 无参全量 | count=**388** = 修复前基线 388，前 5 条 id 逐一相同 | ✅ 兼容 |
| 4 | `?status=running&limit=2` | count=2，statuses={'running'}，组合过滤生效 | ✅ |
| 5 | `?limit=abc` | count=388（全量回退，无报错） | ✅ 非法忽略 |

（响应均先落盘 /tmp/t0450-v*.json 后 python 抽取，原始文件保留可复查）

## 结论
改动仅 server.js `/api/tasks` 处理器内新增 8 行（limit/offset 校验与 LIMIT/OFFSET 追加），
node --check 通过，服务重启 active，5 项验收全过，无默认上限引入，裸调全量行为不变。
