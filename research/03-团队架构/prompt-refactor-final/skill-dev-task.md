# 开发任务质量 SKILL（草稿）

> 保存为：`/root/.openclaw/workspace/skills/dev-task/SKILL.md`
> 触发：spawn 开发/修复类子 agent。任务书结构以 `tools/templates/spawn-task.md` 为唯一模板。

## 模式选择

| 任务 | 模式 |
|---|---|
| 单文件改动 / bug 修复 / 原型 | 直接 spawn 子 agent |
| 多文件 / 复杂功能 / DB schema / 安全相关 | spawn + 分步验证 + 加强约束 |

## 加强约束（写进任务书）

- 3+ 文件：分步执行，每步验收后再下一步。
- DB schema：先给迁移方案，经确认后再改；备份优先。
- 认证/安全代码：完成后主 agent 额外独立验证。
- 子 agent 称“测试失败但已修复”：一律重新 spawn 验证。

## 开发验收四问

1. 是否报告了实际运行的测试/验证结果（不是“应该可以”）？
2. `.task-completions.jsonl` 是否有完成概要？
3. 修改范围是否合理，有无无关文件被改动？
4. 服务/命令是否实跑通过（`node --check` / 服务 active / API 返回）？

## CLAUDE.md 维护纪律

- 每个活跃项目 MUST 有 `CLAUDE.md`（模板：`tools/templates/CLAUDE-template.md`）。
- 目标长度 60–80 行，不超过 200 行。
- 只写非显而易见、linter 无法检查的规则。
- 犯错 → 纠正 → 把规则写进对应项目的 CLAUDE.md。
- 每两周 review，删除过时规则。
